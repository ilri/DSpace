#!/usr/bin/env python3
#
# parse-iso-codes.py v0.0.1
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the Research Organization Registry dataset for organizations read
# from a text file. Text file should have one organization per line. Results
# are saved to a CSV including the organization and whether it matched or not.
#
# This script is written for Python 3.6+.
#

import argparse
import json
import signal
import sys


def choose_country_name(country: dict):
    # Prefer the common name if it exists! Otherwise, prefer the shorter of name
    # and official_name.
    try:
        return country["common_name"]
    except KeyError:
        pass

    try:
        country_name = country["name"]
    except KeyError:
        country_name = False

    try:
        country_official_name = country["official_name"]
    except KeyError:
        country_official_name = False

    if country_name and not country_official_name:
        return country_name

    if country_official_name and not country_name:
        return country_official_name

    if len(country["name"]) < len(country["official_name"]):
        return country["name"]
    else:
        return country["official_name"]


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Parse iso_3166-1.json from Debian's iso-codes package to a list of countries."
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
    help="Path to iso_3166-1.json from Debian iso-codes package.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Name of output file to write results to.",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# read the list of countries
countries_json = json.load(args.input_file)

for country in countries_json["3166-1"]:
    country_name = choose_country_name(country)

    args.output_file.write(f"{country_name}\n")

args.input_file.close()
args.output_file.close()

exit()
