#!/usr/bin/env python3
#
# get_scihub_pdfs.py 0.0.1
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
#   $ pip install colorama requests
#

import argparse
import csv
import os.path
import signal
import re

from colorama import Fore
from scidownl import scihub_download


def signal_handler(signal, frame):
    sys.exit(1)


def download_pdf(doi):
    # Extract actual DOI portion from DOI string, just in case it is a URL, and
    # strip the newline
    doi_stripped = re.sub(r"https?://(dx.)?doi.org/", "", doi).strip()
    # Set filename based on DOI, ie: 10.3402/iee.v6.31191 → 10.3402-iee.v6.31191.pdf
    filename = doi_stripped.replace("/", "-") + ".pdf"

    print(f"Processing {doi_stripped}")

    # check if file exists already
    if os.path.isfile(filename):
        if args.debug:
            print(Fore.GREEN + f"> {filename} already downloaded." + Fore.RESET)
    else:
        if args.debug:
            print(
                Fore.GREEN
                + f"> Attempting to download PDF for {doi_stripped}"
                + Fore.RESET
            )

        scihub_download(doi_stripped, paper_type='doi', out=filename)

    # check if the file was downloaded, since we have no way to know if it was
    # successful.
    if os.path.isfile(filename):
        return filename
    else:
        return ""


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
        "--output-file",
        help="Path to output CSV file.",
        required=True,
        type=argparse.FileType("w"),
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="Do not print progress messages to the screen.",
        action="store_true",
    )
    args = parser.parse_args()

    dois = args.input_file.readlines()

    output_fieldnames = [
        "doi",
        "filename",
    ]
    writer = csv.DictWriter(args.output_file, fieldnames=output_fieldnames)
    writer.writeheader()

    for doi in dois:
        filename = download_pdf(doi)

        writer.writerow(
            {
                "doi": doi.strip(),
                "filename": filename,
            }
        )
