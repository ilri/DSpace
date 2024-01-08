#!/usr/bin/env python3
#
# crossref-funders-lookup.py 0.3.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the public Crossref API for funders read from a text file. Text file
# should have one subject per line.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama requests requests-cache
#

import argparse
import csv
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
from colorama import Fore


# read funders from a text file, one per line
def read_funders_from_file():
    # initialize an empty list for funders
    funders = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add subjects that aren't already present
        if line not in funders:
            funders.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_funders(funders)


def resolve_funders(funders):
    fieldnames = ["funder", "match type", "matched"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # enable transparent request cache with two weeks expiry because I don't
    # know how often Crossref is updated.
    expire_after = timedelta(days=14)
    requests_cache.install_cache("requests-cache", expire_after=expire_after)

    # prune old cache entries
    requests_cache.delete()

    for funder in funders:
        if args.debug:
            sys.stderr.write(Fore.GREEN + f"Looking up funder: {funder}\n" + Fore.RESET)

        request_url = "https://api.crossref.org/funders"
        request_params = {"query": funder}

        if args.email:
            request_params.update(mailto=args.email)

        try:
            request = requests.get(request_url, params=request_params)
        except requests.exceptions.ConnectionError:
            sys.stderr.write(Fore.RED + "Connection error.\n" + Fore.RESET)

        if request.status_code == requests.codes.ok:
            data = request.json()

            # assume no matches yet
            matched = False

            # check if there are any results
            if data["message"]["total-results"] > 0:
                # iterate over each search result (item)
                for item in data["message"]["items"]:
                    if item["name"].lower() == funder.lower() and not matched:
                        matched = True

                        print(
                            f"Exact match for {funder} in Crossref (cached: {request.from_cache})"
                        )

                        writer.writerow(
                            {
                                "funder": funder,
                                "match type": "name",
                                "matched": "true",
                            }
                        )

                        # break out of the items loop because we have a match
                        break

                    # check the alt-names for each search result
                    for altname in item["alt-names"]:
                        if altname.lower() == funder.lower() and not matched:
                            matched = True

                            print(
                                f"Alt-name match for {funder} in Crossref (cached: {request.from_cache})"
                            )

                            writer.writerow(
                                {
                                    "funder": funder,
                                    "match type": "alt-name",
                                    "matched": "true",
                                }
                            )

                            # break out of the alt-name loop because we have a match
                            break

            if data["message"]["total-results"] == 0 or not matched:
                if args.debug:
                    sys.stderr.write(
                        Fore.YELLOW
                        + f"No match for {funder} in Crossref (cached: {request.from_cache})\n"
                        + Fore.RESET
                    )

                writer.writerow(
                    {
                        "funder": funder,
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
    description="Query the Crossref REST API to validate funders from a text file."
)
parser.add_argument(
    "-e",
    "--email",
    help="Contact email to use in API requests so Crossref is more lenient with our request rate.",
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
    help="File name containing funders to look up.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Name of output file (CSV) to write results to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the funders from there
if args.input_file:
    read_funders_from_file()

exit()
