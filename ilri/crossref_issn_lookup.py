#!/usr/bin/env python3
#
# crossref-issn-lookup.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the public Crossref API for journal titles using ISSNs read from a
# text file. The text file should have one ISSN per line.
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


# read journals from a text file, one per line
def read_issns_from_file():
    # initialize an empty list for ISSNs
    issns = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add ISSNs that aren't already present
        if line not in issns:
            issns.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_issns(issns)


def resolve_issns(issns):
    fieldnames = ["issn", "journal title"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # enable transparent request cache with two weeks expiry because I don't
    # know how often Crossref is updated.
    expire_after = timedelta(days=14)
    requests_cache.install_cache("requests-cache", expire_after=expire_after)

    # prune old cache entries
    requests_cache.delete()

    for issn in issns:
        if args.debug:
            sys.stderr.write(Fore.GREEN + f"Looking up ISSN: {issn}\n" + Fore.RESET)

        request_url = f"https://api.crossref.org/journals/{issn}"

        try:
            if args.email:
                request_params = {"mailto": args.email}

                request = requests.get(request_url, params=request_params)
            else:
                request = requests.get(request_url, params=request_params)

        except requests.exceptions.ConnectionError:
            sys.stderr.write(Fore.RED + "Connection error.\n" + Fore.RESET)

        # CrossRef responds 404 if a journal isn't found, so we check for an
        # HTTP 2xx response here
        if request.status_code == requests.codes.ok:
            data = request.json()

            # sanity check if our ISSN is in CrossRef's response (do we
            # need to check lowercase here?)
            if issn in data["message"]["ISSN"]:
                print(
                    f"Exact match for {issn} in Crossref (cached: {request.from_cache})"
                )

                writer.writerow(
                    {"issn": issn, "journal title": data["message"]["title"]}
                )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + f"No match for {issn} in Crossref (cached: {request.from_cache})\n"
                    + Fore.RESET
                )

            writer.writerow({"issn": issn, "journal title": ""})

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the Crossref REST API to validate ISSNs from a text file."
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
    help="File name containing ISSNs to look up.",
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

# if the user specified an input file, get the ISSNs from there
if args.input_file:
    read_issns_from_file()

exit()
