#!/usr/bin/env python
#
# openalex_title_lookup.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the OpenAlex API for titles read from a text file (one per line) in
# order to find DOIs for items.
#
# This script is written for Python 3.11+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#

import argparse
import csv
import logging
import signal
import sys
from datetime import timedelta

import requests
from requests_cache import CachedSession
import util

# Create a local logger instance for this module. We don't do any configuration
# because this module might be used elsewhere that will have its own logging
# configuration.
logger = logging.getLogger(__name__)


def lookup_title(title: str) -> None:
    # Strip here in case the 80th character of the string is a space
    logger.info(f"Looking up: {title[0:80].strip()}...")

    try:
        # OpenAlex filters are 10x cheaper than searches
        params = {
            "filter": f'display_name:"{title}",has_doi:true',
            "api_key": args.api_key,
        }
        url = "https://api.openalex.org/works"
        res = session.get(url, params=params)
    except requests.exceptions.RetryError:
        logger.error("OpenAlex API limit reached! Try again tomorrow.")

        sys.exit(1)

    try:
        results = res.json()["results"]
    except KeyError:
        logger.debug("> No results!")

        return

    for result in results:
        logger.debug(f"> Checking {result['id']}")

        # Wow, some works have no title! For example: https://openalex.org/works/W4321449989
        if not result["title"]:
            logger.debug("> Missing title—this is strange!")

            continue

        if title.lower() != result["title"].lower().strip():
            logger.debug("> Title doesn't match.")

            continue
        else:
            logger.debug("> Found an exact title match.")

            writer.writerow(
                {
                    "title": title,
                    "doi": result["doi"],
                }
            )

            return

    return


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the OpenAlex API for titles in order to find missing DOIs."
)
parser.add_argument(
    "-k",
    "--api-key",
    required=True,
    help="OpenAlex API key.",
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
    help="File name containing titles to look up.",
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


# install a transparent requests cache
expire_after = timedelta(days=30)
session = CachedSession(
    "requests-cache", expire_after=expire_after, allowable_codes=[200]
)

# prune old cache entries
session.cache.delete(expired=True)

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

# Write the CSV header before starting
fieldnames = ["title", "doi"]
writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
writer.writeheader()

titles = args.input_file.readlines()

args.input_file.close()

for title in titles:
    lookup_title(title.strip())

# close output file before we exit
args.output_file.close()
