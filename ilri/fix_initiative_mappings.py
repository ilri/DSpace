#!/usr/bin/env python3
#
# fix-initiative-mappings.py 0.0.2
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# A script to help me fix collection mappings for items tagged with metadata
# for the 2030 Research Initiatives. It works by parsing the DSpace REST API
# to find collection names and handles, then checks existing items to see if
# their tagged Initiatives match their mapped collections. By default, the
# script will add missing mappings, but will not remove invalid ones (see the
# -r option).
#
# The script expects a CSV with item IDs, collections, and Initiatives, and
# outputs a CSV with updated collection mappings that you can import to DSpace
# using `dspace metadata-import -f file.csv`.
#
# You can optionally specify the URL of a DSpace REST application (default is to
# use http://localhost:8080/rest).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install requests requests_cache colorama
#
# See: https://requests.readthedocs.org/en/master
#
# TODO: abstract some stuff so it's less messy

import argparse
import csv
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


def parse_community(community_id):
    request_url = (
        rest_base_url
        + rest_communities_endpoint
        + str(community_id)
        + "?expand=collections"
    )
    try:
        request = requests.get(request_url, headers={"user-agent": rest_user_agent})
    except requests.ConnectionError:
        sys.stderr.write(
            f"{Fore.RED}Could not connect to {args.rest_url}.{Fore.RESET}\n"
        )
        exit(1)

    if request.status_code == requests.codes.ok:
        collections = request.json()["collections"]

        # Initialize an empty dict of Initiative collections
        initiative_collections = {}

        for collection in collections:
            # We are only interested in Initiative collections
            if initiative_column_name_prefix in collection["name"]:
                initiative_collections.update(
                    {collection["name"]: collection["handle"]}
                )
    else:
        sys.stderr.write(
            f"{Fore.RED}Status not OK! Request URL was: {request_url}{Fore.RESET}\n"
        )
        exit(1)

    return initiative_collections


# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

parser = argparse.ArgumentParser(
    description="Find all collections under a given DSpace community."
)
parser.add_argument("community", help="Community to process, for example: 10568/115087")
parser.add_argument("-d", "--debug", help="Print debug messages.", action="store_true")
parser.add_argument(
    "-i",
    "--input-file",
    help="Path to input file (CSV)",
    required=True,
    type=argparse.FileType("r", encoding="UTF-8"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Path to output file (CSV).",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
parser.add_argument(
    "-r", "--remove", help="Remove invalid mappings.", action="store_true"
)
parser.add_argument(
    "-u",
    "--rest-url",
    help="URL of DSpace REST application.",
    default="http://localhost:8080/rest",
)
args = parser.parse_args()

handle = args.community

# REST base URL and endpoints (with leading and trailing slashes)
rest_base_url = args.rest_url
rest_handle_endpoint = "/handle/"
rest_communities_endpoint = "/communities/"
rest_collections_endpoint = "/collections/"
rest_user_agent = "Alan Test Python Requests Bot"
initiatives_list_url = "https://ilri.github.io/cgspace-submission-guidelines/cg-contributor-initiative/cg-contributor-initiative.txt"

# Column names in the CSV
id_column_name = "id"
collection_column_name = "collection"
initiative_column_name = "cg.contributor.initiative[en_US]"
# The prefix for all Initiative collection names
initiative_column_name_prefix = "CGIAR Initiative on "

# Enable transparent request cache with one day expiry, as we are worried that
# Initiative names could have changed.
expire_after = timedelta(days=1)
requests_cache.install_cache("requests-cache", expire_after=expire_after)

# Prune old cache entries
requests_cache.delete()

# Fetch the controlled vocabulary for Initiatives
try:
    request = requests.get(
        initiatives_list_url, headers={"user-agent": rest_user_agent}
    )
except requests.ConnectionError:
    sys.stderr.write(
        f"{Fore.RED}Could not connect to REST API: {args.rest_url}.{Fore.RESET}\n"
    )
    exit(1)

# Convert the request test to a list so we can use it for lookups later
if request.status_code == requests.codes.ok:
    initiatives_list = request.text.splitlines()

# Fetch the metadata for the given community handle
request_url = rest_base_url + rest_handle_endpoint + str(handle)
try:
    request = requests.get(request_url, headers={"user-agent": rest_user_agent})
except requests.ConnectionError:
    sys.stderr.write(
        f"{Fore.RED}Could not connect to REST API: {args.rest_url}.{Fore.RESET}\n"
    )
    exit(1)

# Check the request status
if request.status_code == requests.codes.ok:
    handle_type = request.json()["type"]

    # Make sure the given handle is a community
    if handle_type == "community":
        community_id = request.json()["uuid"]
        initiative_collections = parse_community(community_id)
    else:
        sys.stderr.write(
            +f'{Fore.RED}{handle} is type "{handle_type}", not community.{Fore.RESET}\n'
        )
        exit(1)
else:
    sys.stderr.write(
        f"{Fore.RED}Request failed. Are you sure {handle} is a valid handle?{Fore.RESET}\n"
    )
    exit(1)

# Open the input file
reader = csv.DictReader(args.input_file)

# Check if the columns exist in the input file
if id_column_name not in reader.fieldnames:
    sys.stderr.write(
        f'{Fore.RED}Specified ID column "{id_column_name}" does not exist in the CSV.{Fore.RESET}'
    )
    sys.exit(1)

if collection_column_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'{Fore.RED}Specified collection column "{collection_column_name}" does not exist in the CSV.{Fore.RESET}'
    )
    sys.exit(1)

if initiative_column_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'{Fore.RED}Specified Initiative column "{initiative_column_name}" does not exist in the CSV.{Fore.RESET}'
    )
    sys.exit(1)

# Fields for the output CSV
fieldnames = [
    id_column_name,
    collection_column_name,
]

# Write the CSV header
writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
writer.writeheader()

# Iterate over the input file to check each item's Initiatives and collections
for input_row in reader:
    item_id = input_row[id_column_name]
    # Get the item's current collections
    item_collections = input_row[collection_column_name].split("||")
    item_initiatives = input_row[initiative_column_name].split("||")

    # First, iterate over the item's Initiatives so we can see if it is mapped
    # to appropriate collections.
    for item_initiative in item_initiatives:
        if item_initiative in initiatives_list:
            # This is ugly because our Initiative metadata uses the short
            # names, but the corresponding collection names are prefixed
            # with "CGIAR Initiative on ".
            correct_initiative_collection = initiative_collections[
                f"{initiative_column_name_prefix}{item_initiative}"
            ]

            if correct_initiative_collection in item_collections:
                if args.debug:
                    print(
                        f"{Fore.GREEN}(Phase 1) {item_id} is correctly mapped to Initiative collection: {correct_initiative_collection} ({item_initiative}){Fore.RESET}"
                    )
            else:
                print(
                    f"{Fore.YELLOW}(Phase 1) {item_id} mapping to Initiative collection: {correct_initiative_collection} ({item_initiative}){Fore.RESET}"
                )

                # Add the collection
                item_collections.append(correct_initiative_collection)
        elif not item_initiative:
            if args.debug:
                sys.stderr.write(
                    f"{Fore.RED}(Phase 1) {item_id} has no Initiative metadata{Fore.RESET}\n"
                )
        else:
            sys.stderr.write(
                f"{Fore.RED}(Phase 1) {item_id} has invalid Initiative: {item_initiative}{Fore.RESET}\n"
            )

    # Empty list to hold incorrectly mapped collections we find for this item
    incorrectly_mapped_collections = []

    # Second, iterate over the item's collections to see if each one has corre-
    # sponding Initiative metadata.
    for item_collection in item_collections:
        # Is it an Initiatve collection?
        if item_collection in initiative_collections.values():
            # Now check if this item is tagged with metadata for the corre-
            # sponding Initative. We technically want to do a reverse look-
            # up in the dict to find the key (initiative) for the current
            # collection, but that's not possible. Instead iterate over the
            # dict's keys/values and do some sanity checks.
            for initiative, collection in initiative_collections.items():
                # If current item collection matches the current Initiative
                # collection then we need to check if the Initiative name
                # also matches the item's metadata
                if item_collection == collection:
                    # Remember the collection names use the long Initiative name
                    initiative_short_name = initiative.replace(
                        initiative_column_name_prefix, ""
                    )

                    if initiative_short_name in item_initiatives:
                        if args.debug:
                            print(
                                f"{Fore.GREEN}(Phase 2) {item_id} is correctly mapped to Initiative collection: {collection} ({initiative_short_name}){Fore.RESET}"
                            )

                        continue
                    else:
                        if args.remove:
                            sys.stderr.write(
                                f"{Fore.YELLOW}(Phase 2) {item_id} unmapping from Initiative collection: {collection} ({initiative_short_name}){Fore.RESET}\n"
                            )

                            incorrectly_mapped_collections.append(collection)
                        else:
                            sys.stderr.write(
                                f"{Fore.RED}(Phase 2) {item_id} is incorrectly mapped to Initiative collection: {collection} ({initiative_short_name}){Fore.RESET}\n"
                            )

    for incorrectly_mapped_collection in incorrectly_mapped_collections:
        item_collections.remove(incorrectly_mapped_collection)

    # We only need to save the item to the output CSV if we have changed its
    # mappings. Check the mutated item_collections list against the original
    # from the input CSV.
    if item_collections != input_row[collection_column_name].split("||"):
        # We only need to write the IDs and collections to the output file since we
        # are not modifying any other metadata in the CSV.
        output_row = {
            id_column_name: input_row[id_column_name],
            collection_column_name: "||".join(item_collections),
        }

        writer.writerow(output_row)

# close CSV files before we exit
args.input_file.close()
args.output_file.close()

sys.exit(0)
