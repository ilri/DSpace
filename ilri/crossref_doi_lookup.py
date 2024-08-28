#!/usr/bin/env python3
#
# crossref-doi-lookup.py 0.2.2
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
import logging
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
import util
from colorama import Fore

# Create a local logger instance for this module. We don't do any configuration
# because this module might be used elsewhere that will have its own logging
# configuration.
logger = logging.getLogger(__name__)


# Crossref uses dates with single-digit month and day parts, so we need to pad
# them with zeros if they are less than 10.
def fix_crossref_date(crossref_date: list) -> str:
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


def resolve_doi(doi: str) -> None:
    logger.info(Fore.GREEN + f"Looking up DOI: {doi}" + Fore.RESET)

    # First, check if this DOI is registered at Crossref
    request_url = f"https://api.crossref.org/works/{doi}/agency"
    request_params = {"mailto": args.email}

    try:
        request = requests.get(request_url, params=request_params)
    except requests.exceptions.ConnectionError:
        logger.error(Fore.RED + "Connection error." + Fore.RESET)

        sys.exit(1)

    # HTTP 404 here means the DOI is not registered at Crossref
    if not request.ok:
        logger.debug(
            Fore.YELLOW
            + f"> DOI not in Crossref (cached: {request.from_cache})"
            + Fore.RESET
        )

        return

    data = request.json()

    # Only proceed if this DOI registration agency is Crossref
    match data["message"]["agency"]["label"]:
        case "DataCite":
            logger.debug(
                Fore.YELLOW
                + f"> Skipping DOI registered to DataCite (cached: {request.from_cache})"
                + Fore.RESET
            )

            return
        case "Public":
            logger.debug(
                Fore.YELLOW
                + f'> Skipping DOI registered to "Public" (cached: {request.from_cache})'
                + Fore.RESET
            )

            return
        case "Crossref":
            pass

    # Fetch the metadata for this DOI
    request_url = f"https://api.crossref.org/works/{doi}"
    request_params = {"mailto": args.email}

    try:
        request = requests.get(request_url, params=request_params)
    except requests.exceptions.ConnectionError:
        logger.error(Fore.RED + "Connection error." + Fore.RESET)

    if not request.ok:
        return

    logger.debug(
        Fore.YELLOW + f"> DOI in Crossref (cached: {request.from_cache})" + Fore.RESET
    )

    data = request.json()

    # I don't know why title is an array of strings, but let's just get
    # the first one.
    try:
        title = data["message"]["title"][0]
    except IndexError:
        title = ""

    # Create an empty list to keep our authors
    authors = list()
    affiliations = list()

    try:
        for author in data["message"]["author"]:
            # Some authors have no given name in Crossref
            try:
                # Crossref given name is often initials like "S. M."
                # and we don't want that space!
                author_given_name = author["given"].replace(". ", ".")
            except KeyError:
                author_given_name = None

            # Some authors have no family name in Crossref
            try:
                author_family_name = author["family"]
            except KeyError:
                author_family_name = None

            # Naive construction of "Last, First Initials" when we have
            # both of them.
            if author_family_name and author_given_name:
                authors.append(f"{author_family_name}, {author_given_name}")
            # Otherwise we need to make do with only the family name
            elif author_family_name and author_given_name is None:
                authors.append(author_family_name)
            # And sometimes we need to make do with only the given name
            elif author_given_name and author_family_name is None:
                authors.append(author_given_name)

            # Get any affiliations from the authors (not all have)
            try:
                for affiliation in author["affiliation"]:
                    if affiliation["name"] not in affiliations:
                        affiliations.append(affiliation["name"])
            # Not sure what we can except here
            except:
                pass

    # Believe it or not some items on Crossref have no author (doesn't
    # mean the DOI itself won't, though).
    #
    # See: https://api.crossref.org/works/10.1638/2018-0110
    # See: https://doi.org/10.1638/2018-0110
    except KeyError:
        authors = ""

    # Create an empty list to keep our funders
    funders = list()

    try:
        for funder in data["message"]["funder"]:
            if funder["name"] not in funders:
                funders.append(funder["name"])
    except KeyError:
        pass

    # Get the abstract if it exists
    try:
        abstract = data["message"]["abstract"]
    except KeyError:
        abstract = ""

    # Get the language if it exists
    try:
        language = data["message"]["language"]
    except KeyError:
        language = ""

    try:
        journal = data["message"]["container-title"][0]
    except IndexError:
        journal = ""

    # Create an empty list to hold ISSNs, as there could be more than one
    issns = list()

    # Get the ISSN. For journal articles there is often a print ISSN and
    # an electric ISSN.
    try:
        for issn in data["message"]["ISSN"]:
            issns.append(issn)
    except KeyError:
        issns = ""

    # Create an empty list to hold ISBNs, as there could be more than one
    isbns = list()

    # Get the ISBN. For books and book chapters there is often a print
    # ISBN and an electric ISBN.
    try:
        for isbn in data["message"]["isbn-type"]:
            isbns.append(isbn["value"])
    except KeyError:
        isbns = ""

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

    subjects = list()

    # Get the subjects. Still not sure if these are useful. We should
    # check against AGROVOC before importing.
    try:
        for subject in data["message"]["subject"]:
            subjects.append(subject)
    except KeyError:
        subjects = ""

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
            "title": title,
            "abstract": abstract,
            "language": language,
            "authors": "||".join(authors),
            "affiliations": "||".join(affiliations),
            "funders": "||".join(funders),
            "doi": f"https://doi.org/{doi}",
            "journal": journal,
            "issn": "||".join(issns),
            "isbn": "||".join(isbns),
            "publisher": publisher,
            "volume": volume,
            "issue": issue,
            "page": page,
            "type": item_type,
            "issued": issued,
            "published_print": published_print,
            "published_online": published_online,
            "license": license_url,
            "subjects": "||".join(subjects),
        }
    )


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

# The default log level is WARNING, but we want to set it to DEBUG or INFO
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Since we're running interactively we can set the preferred log format for
# the logging module during this invocation.
logging.basicConfig(format="[%(levelname)s] %(message)s")

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# install a transparent requests cache
expire_after = timedelta(days=30)
requests_cache.install_cache(
    "requests-cache", expire_after=expire_after, allowable_codes=(200, 404)
)
# prune old cache entries
requests_cache.delete()

# Write the CSV header before starting
if args.output_file:
    fieldnames = [
        "title",
        "abstract",
        "language",
        "authors",
        "affiliations",
        "funders",
        "doi",
        "journal",
        "issn",
        "isbn",
        "publisher",
        "volume",
        "issue",
        "page",
        "type",
        "issued",
        "published_print",
        "published_online",
        "license",
        "subjects",
    ]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

# if the user specified an input file, get the DOIs from there
if args.input_file:
    dois = util.read_dois_from_file(args.input_file)
    for doi in dois:
        resolve_doi(doi)

# close output file before we exit
args.output_file.close()
