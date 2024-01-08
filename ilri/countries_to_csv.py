#!/usr/bin/env python3
#
# countries-to-csv.py v0.0.3
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Read a list of countries and export a CSV with their ISO 3166-1 Alpha-2 codes
# and names. Run like this:
#
#  $ countries-to-csv.py input-file.txt output-file.csv
#
# Expects input file to have one country per line. Extract countries from the
# DSpace input-forms.xml with xmllint:
#
#   $ xmllint --xpath '//value-pairs[@value-pairs-name="countrylist"]/pair/stored-value/node()' dspace/config/input-forms.xml > /tmp/cgspace-countries.txt

import csv
import sys

import pycountry

try:
    # Quick handling of command line args, no time to implement argparse.
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
except IndexError:
    print("Please specify input and output files.")

    exit(1)

with open(input_filename, "r") as countries_in:
    with open(output_filename, mode="w") as countries_out:
        # Prepare the CSV
        fieldnames = ["alpha2", "Name"]
        csv_writer = csv.DictWriter(countries_out, fieldnames=fieldnames)
        csv_writer.writeheader()

        for line in countries_in.readlines():
            print(f"Looking up {line.strip()}...")

            country_result = pycountry.countries.get(name=line.strip())

            # Check if we found an exact match first
            if country_result is not None:
                country_alpha2 = country_result.alpha_2
                country_name = line.strip()
            else:
                # Can't find a match so just save the name with no alpha2. Note
                # that we could try with a fuzzy search before giving up, but I
                # have had some strange issues with fuzzy search in the past.
                #
                # See: https://github.com/flyingcircusio/pycountry/issues/115
                country_alpha2 = ""
                country_name = line.strip()

            csv_writer.writerow({"alpha2": country_alpha2, "Name": country_name})
