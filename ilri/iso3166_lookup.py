#!/usr/bin/env python3
#
# iso3166-lookup.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the ISO 3166 dataset for countries read from a text file. Text file
# should have one organization per line. Results are saved to a CSV including
# the country name, whether it matched or not, and the type of match.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama pycountry requests requests-cache
#

import argparse
import csv
import signal
import sys

import pycountry
from colorama import Fore


# read countries from a text file, one per line
def read_countries_from_file():
    # initialize an empty list for countries
    countries = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add organization that aren't already present
        if line not in countries:
            countries.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_countries(countries)


def resolve_countries(countries):
    fieldnames = ["country", "match type", "matched"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    for country in countries:
        if args.debug:
            sys.stderr.write(
                Fore.GREEN + f"Looking up the country: {country!r}\n" + Fore.RESET
            )

        # check for exact match
        if country.lower() in country_names:
            print(f"Name match for {country!r}")

            writer.writerow(
                {"country": country, "match type": "name", "matched": "true"}
            )
        elif country.lower() in country_official_names:
            print(f"Official name match for {country!r}")

            writer.writerow(
                {"country": country, "match type": "official_name", "matched": "true"}
            )
        elif country.lower() in country_common_names:
            print(f"Common name match for {country!r}")

            writer.writerow(
                {
                    "country": country,
                    "match type": "common_name",
                    "matched": "true",
                }
            )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW + f"No match for {country!r}\n" + Fore.RESET
                )

            writer.writerow(
                {
                    "country": country,
                    "match type": "",
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
    description="Query ISO 3166-1 to validate countries from a text file and save results in a CSV."
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
    help="File name containing countries to look up in ISO 3166-1 and ISO 3166-3.",
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

# create empty lists to hold country names
country_names = []
country_official_names = []
country_common_names = []

# iterate over countries and append names to the appropriate lists. We can't use
# a list comprehension here because some countries don't have official_name, etc
# and they raise an AttributeError. Anyways, it's more efficient to iterate over
# the list of countries just once.
for country in pycountry.countries:
    country_names.append(country.name.lower())

    try:
        country_official_names.append(country.official_name.lower())
    except AttributeError:
        pass

    try:
        country_common_names.append(country.common_name.lower())
    except AttributeError:
        pass

# Add names for historic countries from ISO 3166-3
for country in pycountry.historic_countries:
    country_names.append(country.name.lower())

    try:
        country_official_names.append(country.official_name.lower())
    except AttributeError:
        pass

    try:
        country_common_names.append(country.common_name.lower())
    except AttributeError:
        pass

read_countries_from_file()

exit()
