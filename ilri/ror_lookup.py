#!/usr/bin/env python3
#
# ror-lookup.py 0.1.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the Research Organization Registry dataset for organizations read
# from a text file. Text file should have one organization per line. Results
# are saved to a CSV including the organization and whether it matched or not.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama
#

import argparse
import csv
import json
import logging
import signal
import sys

from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)
# Set the global log format
logging.basicConfig(format="[%(levelname)s] %(message)s")


# read organizations from a text file, one per line
def read_organizations_from_file():
    # initialize an empty list for organization
    organizations = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add organization that aren't already present
        if line not in organizations:
            organizations.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_organizations(organizations)


def resolve_organizations(organizations):
    fieldnames = ["organization", "match type", "matched"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    for organization in organizations:
        logger.debug(f"Looking up the organization: {organization}")

        # check for exact match
        if organization.lower() in ror_names:
            logger.info(
                f"{Fore.GREEN}Name match for {organization!r} in ROR{Fore.RESET}"
            )

            writer.writerow(
                {
                    "organization": organization,
                    "match type": "name",
                    "matched": "true",
                }
            )
        elif organization.lower() in ror_aliases:
            logger.info(
                f"{Fore.GREEN}Alias match for {organization!r} in ROR{Fore.RESET}"
            )

            writer.writerow(
                {
                    "organization": organization,
                    "match type": "alias",
                    "matched": "true",
                }
            )
        elif organization.lower() in ror_acronyms:
            logger.info(
                f"{Fore.GREEN}Acronym match for {organization!r} in ROR{Fore.RESET}"
            )

            writer.writerow(
                {
                    "organization": organization,
                    "match type": "acronym",
                    "matched": "true",
                }
            )
        else:
            logger.debug(
                f"{Fore.YELLOW}No match for {organization!r} in ROR{Fore.RESET}"
            )

            writer.writerow(
                {
                    "organization": organization,
                    "match type": "",
                    "matched": "false",
                }
            )

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the ROR JSON to validate organizations from a text file and save results in a CSV."
)
parser.add_argument(
    "-d",
    "--debug",
    help="Set log level to DEBUG.",
    action="store_true",
)
parser.add_argument(
    "-i",
    "--input-file",
    help="File name containing organizations to look up.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-r",
    "--ror-json",
    help="ror.json file containing organizations to look up. See: https://doi.org/10.6084/m9.figshare.c.4596503.v5",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Name of output file to write results to (CSV).",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# The default log level is WARNING, but we want to set it to DEBUG or INFO
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# if the user specified an input file, get the organizations from there
if args.input_file and args.ror_json:
    ror = json.load(args.ror_json)

    # list comprehension instead of a for loop to extract all names
    ror_names = [org["name"].lower() for org in ror]

    # nested list comprehension to extract aliases, think of it like:
    #     ror_aliases_all = []
    #     for org in ror:
    #         for alias in org['aliases']:
    #             ror_aliases_all.append(alias)
    #
    # See: https://stackoverflow.com/questions/18072759/list-comprehension-on-a-nested-list
    ror_aliases_all = [alias.lower() for org in ror for alias in org["aliases"]]
    # dedupe the list by converting it to a dict and back to a list (dicts can't
    # have any duplicate items)
    ror_aliases = list(dict.fromkeys(ror_aliases_all))
    # delete the list of all aliases
    del ror_aliases_all

    # same for acronyms
    ror_acronyms_all = [acronym.lower() for org in ror for acronym in org["acronyms"]]
    ror_acronyms = list(dict.fromkeys(ror_acronyms_all))
    del ror_acronyms_all

    read_organizations_from_file()

exit()
