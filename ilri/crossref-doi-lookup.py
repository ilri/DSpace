#!/usr/bin/env python3
#
# crossref-doi-lookup.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the public Crossref API for DOIs read from a text file (one per line).
# The Crossref database has a wealth of information about DOIs, for example the
# issue date, license, journal title, item type, authors, funders, etc. This
# information can be used to improve metadata in other systems.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama requests requests-cache
#

import argparse
import csv
import re
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
from colorama import Fore


# read DOIs from a text file, one per line
def read_dois_from_file():

    # initialize an empty list for DOIs
    dois = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # trim http://, https://, etc to make sure we only get the DOI component
        line = re.sub(r"^https?://(dx\.)?doi\.org/", "", line)

        # iterate over results and add DOIs that aren't already present
        if line not in dois:
            dois.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_dois(dois)


# Crossref uses dates with single-digit month and day parts, so we need to pad
# them with zeros if they are less than 10.
def fix_crossref_date(crossref_date):
    if len(crossref_date) == 1:
        issued = crossref_date[0]
    elif len(crossref_date) == 2:
        if crossref_date[1] < 10:
            crossref_date_month = f"0{crossref_date[1]}"
        else:
            crossref_date_month = crossref_date[1]

        issued = f"{crossref_date[0]}-{crossref_date_month}"
    elif len(crossref_date) == 3:
        if crossref_date[1] < 10:
            crossref_date_month = f"0{crossref_date[1]}"
        else:
            crossref_date_month = crossref_date[1]

        if crossref_date[2] < 10:
            crossref_date_day = f"0{crossref_date[2]}"
        else:
            crossref_date_day = crossref_date[2]

        issued = f"{crossref_date[0]}-{crossref_date_month}-{crossref_date_day}"
    else:
        issued = ""

    return issued


def resolve_dois(dois):
    fieldnames = [
        "doi",
        "journal",
        "publisher",
        "volume",
        "issue",
        "page",
        "type",
        "issued",
        "published_print",
        "published_online",
        "license",
    ]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    expire_after = timedelta(days=30)
    requests_cache.install_cache("requests-cache", expire_after=expire_after)

    # prune old cache entries
    requests_cache.remove_expired_responses()

    for doi in dois:
        if args.debug:
            sys.stderr.write(Fore.GREEN + f"Looking up DOI: {doi}\n" + Fore.RESET)

        request_url = f"https://api.crossref.org/works/{doi}"
        request_params = {"mailto": args.email}

        try:
            request = requests.get(request_url, params=request_params)
        except requests.exceptions.ConnectionError:
            sys.stderr.write(Fore.RED + f"Connection error.\n" + Fore.RESET)

        if request.status_code == requests.codes.ok:
            if args.debug:
                sys.stdout.write(
                    Fore.YELLOW
                    + f"> DOI in Crossref (cached: {request.from_cache})\n"
                    + Fore.RESET
                )

            data = request.json()

            # Get the journal title. This is interesting, but not very useful
            # because many of the names I've seen were shortened, truncated,
            # or abbreviated. Also, I'm not sure if there can be more than one
            # of these because it's a list (and I'm only getting the first).
            try:
                journal = data["message"]["short-container-title"][0]
            except IndexError:
                journal = ""

            try:
                publisher = data["message"]["publisher"]
            except KeyError:
                publisher = ""

            try:
                volume = data["message"]["volume"]
            except KeyError:
                volume = ""

            try:
                issue = data["message"]["issue"]
            except KeyError:
                issue = ""

            try:
                page = data["message"]["page"]
            except KeyError:
                page = ""

            try:
                item_type = data["message"]["type"]
            except KeyError:
                item_type = ""

            # It appears that *all* DOIs on Crossref have an "issued" date. This
            # is the earliest of the print and online publishing dates. For now
            # I will capture this so I can explore its implications and relation
            # to other dates with real items in the repository.
            #
            # See: https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md
            issued = fix_crossref_date(data["message"]["issued"]["date-parts"][0])

            # Date on which the work was published in print. Apparently not all
            # DOIs have this so we need to try/except. Also note that there is
            # a similar date in ["journal-issue"]["published-print"], but in my
            # experience it is the same as this one 99% of the time when it is
            # present (that's in 10,000 DOIs I checked in 2023-02).
            try:
                published_print = fix_crossref_date(
                    data["message"]["published-print"]["date-parts"][0]
                )
            except KeyError:
                published_print = ""

            # Date on which the work was published online. Note again that there
            # is also ["journal-issue"]["published-online"], but in my experience
            # it is only present ~33% of the time, and is only 50% the same as
            # published-online. For now I'm not sure what to make of that, so I
            # will not use it.
            try:
                published_online = fix_crossref_date(
                    data["message"]["published-online"]["date-parts"][0]
                )
            except KeyError:
                published_online = ""

            # Not all items have licenses, and some have multiple licenses. We
            # will check for licenses in the order we prefer them: am, vor, tdm,
            # and unspecified. These correspond to: accepted manuscript, version
            # of record, text and data mining, and unspecified. I'm curious if
            # there is *ever* a case where we would want the tdm license...? Can
            # these ever be CC if the others are missing?
            doi_licenses = {}
            try:
                for doi_license in data["message"]["license"]:
                    content_version = doi_license["content-version"]
                    doi_licenses[content_version] = doi_license["URL"]

                if "am" in doi_licenses:
                    license_url = f'am: {doi_licenses["am"]}'
                elif "vor" in doi_licenses:
                    license_url = f'vor: {doi_licenses["vor"]}'
                elif "tdm" in doi_licenses:
                    license_url = f'tdm: {doi_licenses["tdm"]}'
                else:
                    license_url = f'unspecified: {doi_licenses["unspecified"]}'
            except KeyError:
                license_url = ""

            writer.writerow(
                {
                    "doi": doi,
                    "journal": journal,
                    "publisher": publisher,
                    "volume": volume,
                    "issue": issue,
                    "page": page,
                    "type": item_type,
                    "issued": issued,
                    "published_print": published_print,
                    "published_online": published_online,
                    "license": license_url,
                }
            )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + f"DOI not in Crossref (cached: {request.from_cache})\n"
                    + Fore.RESET
                )

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the Crossref REST API for metadata about DOIs."
)
parser.add_argument(
    "-e",
    "--email",
    required=True,
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
    help="File name containing DOIs to look up.",
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

# if the user specified an input file, get the DOIs from there
if args.input_file:
    read_dois_from_file()

exit()
