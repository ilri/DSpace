#!/usr/bin/env python3
#
# ror-lookup.py 0.0.2
#
# Copyright 2020 Alan Orth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
#   $ pip install colorama requests requests-cache
#

import argparse
from colorama import Fore
import csv
import json
import signal
import sys


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


    fieldnames = ["organization", "matched"]
def resolve_organizations(organizations):
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    for organization in organizations:
        if args.debug:
            sys.stderr.write(
                Fore.GREEN
                + f"Looking up the organization: {organization})\n"
                + Fore.RESET
            )

        # check for exact match
        if organization.lower() in ror_names:
            print(f"Match for {organization!r} in ROR)")

            writer.writerow(
                {"organization": organization, "matched": "true",}
            )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + f"No match for {organization!r} in ROR)\n"
                    + Fore.RESET
                )

            writer.writerow(
                {"organization": organization, "matched": "false",}
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
    help="Print debug messages to standard error (stderr).",
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

# if the user specified an input file, get the organizations from there
if args.input_file and args.ror_json:
    ror = json.load(args.ror_json)

    # list comprehension instead of a for loop to extract all names
    ror_names = [org["name"].lower() for org in ror]

    read_organizations_from_file()

exit()
