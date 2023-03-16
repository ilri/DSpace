#!/usr/bin/env python3
#
# subdivision-lookup.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the pycountry ISO 3166-2 dataset for subdivisions read from a text
# file. Text file should have one subdivision per line. Results are saved to
# a CSV including the subdivision and whether it matched or not.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama pycountry
#

import argparse
import csv
import signal
import sys

import pycountry
from colorama import Fore


# read subdivisions from a text file, one per line
def read_subdivisions_from_file():
    # initialize an empty list for subdivisions
    subdivisions = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add subdivisions that aren't already present
        if line not in subdivisions:
            subdivisions.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_subdivisions(subdivisions)


def resolve_subdivisions(subdivisions):
    fieldnames = ["subdivision", "matched"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    for subdivision in subdivisions:
        if args.debug:
            sys.stderr.write(
                Fore.GREEN + f"Looking up the subdivision: {subdivision}\n" + Fore.RESET
            )

        # check for exact match
        if subdivision.lower() in subdivision_names:
            print(f"Match for {subdivision!r}")

            writer.writerow(
                {
                    "subdivision": subdivision,
                    "matched": "true",
                }
            )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW + f"No match for {subdivision!r}\n" + Fore.RESET
                )

            writer.writerow(
                {
                    "subdivision": subdivision,
                    "matched": "false",
                }
            )

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query pycountry's ISO 3166-2 list to validate subdivisions from a text file and save results in a CSV."
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
    help="File name containing subdivisions to look up.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Name of output file to write results to (CSV).",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# list comprehension instead of a for loop to extract all subdivision names
subdivision_names = [subdivision.name.lower() for subdivision in pycountry.subdivisions]

read_subdivisions_from_file()

exit()
