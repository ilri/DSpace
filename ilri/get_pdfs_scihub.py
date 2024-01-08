#!/usr/bin/env python3
#
# get_pdfs_scihub.py 0.0.3
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Attempts to download PDFs for given DOIs from Sci-Hub. We only do this for
# items we know are licensed Creative Commons (though not "ND"). The idea is
# to download the PDFs in order to create and upload thumbnails to CGSpace,
# not to upload the PDFs themselves (yet?).
#
# Input file should have one DOI per line, for example:
#
#  https://doi.org/10.5194/bg-18-1481-2021
#  https://doi.org/10.5194/gmd-14-3789-2021
#
# This script is written for Python 3.7+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama scidownl
#

import argparse
import csv
import logging
import os.path
import signal
import sys

import util
from colorama import Fore
from scidownl import scihub_download

# Create a local logger instance
logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(1)


def download_pdf(doi):
    logger.info(f"Processing {doi}")

    filename = doi.replace("/", "-") + ".pdf"
    filename = os.path.join(args.output_directory, filename)

    # check if file exists already
    if os.path.isfile(filename):
        logger.debug(Fore.GREEN + f"> {filename} already downloaded." + Fore.RESET)

        return
    else:
        logger.debug(
            Fore.GREEN + f"> Attempting to download PDF for {doi}" + Fore.RESET
        )

        scihub_download(doi, paper_type="doi", out=filename)

    # check if the file was downloaded, since we have no way to know if it was
    # successful.
    if os.path.isfile(filename):
        logger.info(Fore.YELLOW + f"> Successfully saved to: {filename}" + Fore.RESET)
    else:
        logger.debug(Fore.RED + "> Download unsuccessful." + Fore.RESET)


if __name__ == "__main__":
    # set the signal handler for SIGINT (^C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description="Download PDFs from Sci-Hub.")
    parser.add_argument(
        "-i",
        "--input-file",
        help="Path to input file.",
        required=True,
        type=argparse.FileType("r", encoding="UTF-8"),
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print debug messages to standard error (stderr).",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Name of directory to save files.",
        required=False,
        default=".",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="Do not print progress messages to the screen.",
        action="store_true",
    )
    args = parser.parse_args()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set the global log format
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    dois = util.read_dois_from_file(args.input_file)

    for doi in dois:
        download_pdf(doi)
