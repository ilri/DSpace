#!/usr/bin/env python3
#
# generate-thumbnails.py 1.1.4
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---

# Reads the filename and URL fields from a CSV, fetches the PDF, and generates
# a thumbnail using pyvips (libvips must be installed on the host).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama requests pyvips
#
# See: https://requests.readthedocs.org/en/master

import argparse
import csv
import os.path
import re
import signal
import sys

import pyvips
import requests
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


# Process thumbnails from filename.pdf to filename.webp using libvips. Equivalent
# to the following shell invocation:
#
#    vipsthumbnail 64661.pdf -s 600 -o '%s.webp[Q=89,strip]'
#
# vips is faster than GraphicsMagick/ImageMagick, uses less memory, and seems
# to generate better quality images. Note that libvips uses poppler instead of
# Ghostscript, which means that CMYK colorspace is not supported. We might need
# to do something about that...
#
# See: https://github.com/libvips/libvips/issues/379
def create_thumbnail(row):
    filename = row[args.filename_field_name]
    thumbnail = os.path.splitext(filename)[0] + ".webp"
    # check if the file has been downloaded
    if not os.path.isfile(filename):
        if args.debug:
            print(f"{Fore.YELLOW}> Missing {filename}.{Fore.RESET}")
    # check if we already have a thumbnail
    elif os.path.isfile(thumbnail):
        if args.debug:
            print(
                f"{Fore.YELLOW}> Thumbnail for {filename} already exists.{Fore.RESET}"
            )
    else:
        print(f"{Fore.GREEN}> Creating thumbnail for {filename}...{Fore.RESET}")
        vips_image = pyvips.Image.new_from_file(filename, access="sequential")
        # Set max height to 600px
        vips_thumbnail = vips_image.thumbnail_image(600)
        vips_thumbnail.webpsave(thumbnail, Q=89, strip=True)

    return


def download_bitstream(row):
    request_headers = {"user-agent": "CGSpace PDF bot"}

    # some records have multiple URLs separated by "||"
    pattern = re.compile(r"\|\|")
    urls = pattern.split(row[args.url_field_name])
    filenames = pattern.split(row[args.filename_field_name])
    for url, filename in zip(urls, filenames):
        if args.debug:
            print(f"URL: {url}")
            print(f"File: {filename}")

        # check if file exists
        if os.path.isfile(filename):
            if args.debug:
                print(Fore.YELLOW + f"> {filename} already downloaded." + Fore.RESET)
        else:
            if args.debug:
                print(Fore.GREEN + f"> Downloading {filename}..." + Fore.RESET)

            response = requests.get(url, headers=request_headers, stream=True)
            if response.status_code == 200:
                with open(filename, "wb") as fd:
                    for chunk in response:
                        fd.write(chunk)
            else:
                print(
                    Fore.RED
                    + f"> Download failed (HTTP {response.status_code}), I will try again next time."
                    + Fore.RESET
                )

    return


if __name__ == "__main__":
    # set the signal handler for SIGINT (^C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Download PDFs and generate thumbnails from files in a CSV."
    )
    parser.add_argument(
        "-i",
        "--csv-file",
        help="Path to CSV file",
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
        "-n",
        "--dry-run",
        help="Only print changes that would be made.",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--filename-field-name",
        help="Name of column with thumbnail filenames.",
        default="filename",
    )
    parser.add_argument(
        "-u",
        "--url-field-name",
        help="Name of column with URLs for the PDFs.",
        default="dc.description.url",
    )
    parser.add_argument(
        "-w", "--download-only", help="Only download the PDFs.", action="store_true"
    )
    args = parser.parse_args()

    # open the CSV
    reader = csv.DictReader(args.csv_file)

    # check if the filename and URL fields specified by the user exist in the CSV
    if args.filename_field_name not in reader.fieldnames:
        sys.stderr.write(
            f"{Fore.RED}Specified field '{args.filename_field_name}' does not exist in the CSV.\n{Fore.RESET}"
        )
        sys.exit(1)
    if args.url_field_name not in reader.fieldnames:
        sys.stderr.write(
            f"{Fore.RED}Specified field '{args.url_field_name}' does not exist in the CSV.\n{Fore.RESET}"
        )
        sys.exit(1)

    rows_to_process = [
        row
        for row in reader
        if row[args.url_field_name] and row[args.filename_field_name]
    ]

    for row in rows_to_process:
        download_bitstream(row)

        if args.download_only is not True:
            create_thumbnail(row)
