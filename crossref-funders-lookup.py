#!/usr/bin/env python3
#
# crossref-funders-lookup.py 0.1.0
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
# Queries the public CrossRef API for funders read from a text file. Text file
# should have one subject per line.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama requests requests-cache
#

import argparse
from colorama import Fore
from datetime import timedelta
import re
import requests
import requests_cache
import signal
import sys
import urllib.parse


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

    # enable transparent request cache with two weeks expiry because I don't
    # know how often CrossRef is updated.
    expire_after = timedelta(days=14)
    requests_cache.install_cache(
        "crossref-response-cache", expire_after=expire_after
    )

    # prune old cache entries
    requests_cache.core.remove_expired_responses()

    for funder in funders:

        if args.debug:
            sys.stderr.write(Fore.GREEN + f"Looking up funder: {funder}\n" + Fore.RESET)

        request_url = "https://api.crossref.org/funders"
        request_params = {'query': funder}

        if args.email:
            request_params.update(mailto = args.email)

        try:
            request = requests.get(request_url, params=request_params)
        except requests.exceptions.ConnectionError:
            sys.stderr.write(Fore.RED + f"Connection error.\n" + Fore.RESET)

        if request.status_code == requests.codes.ok:
            data = request.json()

            # assume no matches yet
            matched = False

            # check if there are any results
            if data["message"]["total-results"] > 0:
                # iterate over each search result (item)
                for item in data["message"]["items"]:
                    if item["name"] == funder and not matched:
                        matched = True

                        print(
                            f"Exact match for {funder} in CrossRef (matched: {matched})"
                        )

                        args.output_matches_file.write(funder + "\n")

                        # break out of the items loop because we have a match
                        break

                    # check the alt-names for each search result
                    for altname in item["alt-names"]:
                        if altname == funder and not matched:
                            matched = True

                            print(
                                f"Alt-name match for {funder} in CrossRef (matched: {matched})"
                            )

                            args.output_matches_file.write(funder + "\n")

                            # break out of the altname loop because we have a match
                            break

            if data["message"]["total-results"] == 0 or not matched:
                if args.debug:
                    sys.stderr.write(
                        Fore.YELLOW
                        + f"No match for {funder} in CrossRef\n"
                        + Fore.RESET
                    )

                args.output_rejects_file.write(funder + "\n")

    # close output files before we exit
    args.output_matches_file.close()
    args.output_rejects_file.close()


def signal_handler(signal, frame):
    # close output files before we exit
    args.output_matches_file.close()
    args.output_rejects_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the CrossRef REST API to validate fundersfrom a text file."
)
parser.add_argument(
    "-e",
    "--email",
    help="Contact email to use in API requests so CrossRef is more lenient with our request rate.",
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
    "-om",
    "--output-matches-file",
    help="Name of output file to write matched funders to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
parser.add_argument(
    "-or",
    "--output-rejects-file",
    help="Name of output file to write rejected funders to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the addresses from there
if args.input_file:
    read_funders_from_file()

exit()
