#!/usr/bin/env python3
#
# get_pdfs_unpaywall.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the public Unpaywall API for DOIs read from a text file, one per line,
# and attempts to download fulltext PDFs.
#
import argparse
import logging
import os
import re
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
import util
from colorama import Fore

# Create a root logger instance so that submodules can inherit our config.
# See: https://gist.github.com/gene1wood/73b715434c587d2240c21fc83fad7962#explanation-of-the-relationship-between-python-logging-root-logger-and-other-loggers
logger = logging.getLogger()


def resolve_doi(doi: str) -> None:
    logger.info(f"Looking up DOI: {doi}")

    # Set filename based on DOI so we can check whether it has already been
    # downloaded, ie: 10.3402/iee.v6.31191 → 10.3402-iee.v6.31191.pdf
    pdf_filename = doi.replace("/", "-") + ".pdf"
    pdf_file_path = os.path.join(args.output_directory, pdf_filename)

    # Check if file exists already so we can return early if so
    if os.path.isfile(pdf_file_path):
        logger.debug(Fore.GREEN + f"> {pdf_file_path} already downloaded." + Fore.RESET)

        return

    # Fetch the metadata for this DOI
    request_url = f"https://api.unpaywall.org/v2/{doi}"
    request_params = {"email": args.email}

    try:
        request = requests.get(request_url, params=request_params)
    except requests.exceptions.ConnectionError:
        logger.error(Fore.RED + "Connection error." + Fore.RESET)

        # I guess we have to exit
        sys.exit(1)

    # Fail early if the DOI is not found in Unpaywall
    if not request.ok:
        logger.debug(f"> DOI not in Unpaywall (cached: {request.from_cache})")

        return

    logger.debug(f"> DOI in Unpaywall (cached: {request.from_cache})")

    data = request.json()

    file_downloaded = False
    for oa_location in data["oa_locations"]:
        if not file_downloaded:
            try:
                url_for_pdf = oa_location["url_for_pdf"]

                # Make sure there is actually something here, sometimes
                # the value is blank! Bail out early to check the next
                # source
                if not url_for_pdf:
                    continue

                logger.info(
                    Fore.YELLOW
                    + f"> Attempting to download: {url_for_pdf}"
                    + Fore.RESET
                )

                # Try to download the file from this OA location
                if util.download_file(url_for_pdf, pdf_file_path):
                    logger.info(
                        Fore.YELLOW
                        + f"> Successfully saved to: {pdf_file_path}"
                        + Fore.RESET
                    )

                    file_downloaded = True
                else:
                    logger.debug(Fore.RED + "> Download unsuccessful." + Fore.RESET)

                    # I guess this OA location is stale
                    file_downloaded = False
            except:
                # no PDF URL in this oa_location, try the next
                continue


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the Unpaywall REST API for metadata about DOIs."
)
parser.add_argument(
    "-e",
    "--email",
    required=True,
    help="Contact email to use in API requests so Unpaywall is more lenient with our request rate.",
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
    "--output-directory",
    help="Name of directory to save files.",
    required=False,
    default=".",
)
args = parser.parse_args()

# Since we are running interactively we can override the log level and format.
# The default log level is WARNING, but we want to set it to DEBUG or INFO.
if args.debug:
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(format="[D] %(message)s")
else:
    logger.setLevel(logging.INFO)
    logging.basicConfig(format="[I] %(message)s")

# Install a transparent request cache
expire_after = timedelta(days=30)
requests_cache.install_cache(
    "requests-cache", expire_after=expire_after, allowable_codes=(200, 404)
)
requests_cache.delete()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the DOIs from there
if args.input_file:
    dois = util.read_dois_from_file(args.input_file)
    for doi in dois:
        resolve_doi(doi)
