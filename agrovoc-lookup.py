#!/usr/bin/env python3
#
# agrovoc-lookup.py 0.2.2
#
# Copyright 2019 Alan Orth.
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
# Queries the public AGROVOC API for subjects read from a text file. Text file
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


# read subjects from a text file, one per line
def read_subjects_from_file():

    # initialize an empty list for subjects
    subjects = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add subjects that aren't already present
        if line not in subjects:
            subjects.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_subjects(subjects)


def resolve_subjects(subjects):

    for subject in subjects:
        if args.debug:
            sys.stderr.write(
                Fore.GREEN
                + f"Looking up the subject: {subject} ({args.language})\n"
                + Fore.RESET
            )

        # We urlencode the subject before adding it to the request URL to handle
        # URLs with special characters, for example:
        # WOMEN'S PARTICIPATION
        # COMMUNITY-BASED FOREST MANAGEMENT
        # INTERACCIÓN GENOTIPO AMBIENTE
        # COCOA (PLANT)
        request_url = f"http://agrovoc.uniroma2.it/agrovoc/rest/v1/agrovoc/search?query={urllib.parse.quote(subject)}&lang={args.language}"

        # enable transparent request cache with seven days expiry
        expire_after = timedelta(days=30)
        requests_cache.install_cache(
            "agrovoc-response-cache", expire_after=expire_after
        )

        request = requests.get(request_url)

        # prune old cache entries
        requests_cache.core.remove_expired_responses()

        if request.status_code == requests.codes.ok:
            data = request.json()

            # check if there is 1 result, ie an exact subject term match
            if len(data["results"]) == 1:
                print(f"Exact match for {subject!r} in AGROVOC {args.language}")

                args.output_matches_file.write(subject + "\n")
            else:
                if args.debug:
                    sys.stderr.write(
                        Fore.YELLOW
                        + f"No exact match for {subject!r} in AGROVOC {args.language}\n"
                        + Fore.RESET
                    )

                args.output_rejects_file.write(subject + "\n")

    # close output files before we exit
    args.output_matches_file.close()
    args.output_rejects_file.close()


def signal_handler(signal, frame):
    # close output files before we exit
    args.output_matches_file.close()
    args.output_rejects_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the AGROVOC REST API to validate subject terms from a text file."
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
    help="File name containing subject terms to look up.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-l", "--language", help="Language to query terms (default en).", default="en"
)
parser.add_argument(
    "-om",
    "--output-matches-file",
    help="Name of output file to write matched subjects to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
parser.add_argument(
    "-or",
    "--output-rejects-file",
    help="Name of output file to write rejected subjects to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the addresses from there
if args.input_file:
    read_subjects_from_file()

exit()
