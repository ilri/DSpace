#!/usr/bin/env python3
#
# rest-find-collections.py 1.1.3
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# A quick and dirty example for parsing the DSpace REST API to find and print
# the names of all collections contained in a community hierarchy. It expects
# exactly one command line argument: the handle of a community. For example:
#
#   $ ./rest-find-collections.py 10568/1
#
# You can optionally specify the URL of a DSpace REST application (default is to
# use http://localhost:8080/rest).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install requests colorama
#
# See: https://requests.readthedocs.org/en/master

import argparse
import signal
import sys

import requests
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


def parse_community(community_id):
    request_url = (
        rest_base_url
        + rest_communities_endpoint
        + str(community_id)
        + "?expand=collections,subCommunities"
    )
    try:
        request = requests.get(request_url, headers={"user-agent": rest_user_agent})
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED + "Could not connect to {0}.\n".format(args.rest_url) + Fore.RESET
        )
        exit(1)

    if request.status_code == requests.codes.ok:
        subcommunities = request.json()["subcommunities"]
        collections = request.json()["collections"]

        for subcommunity in subcommunities:
            subcommunity_id = subcommunity["uuid"]

            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + "Found subcommunity (id: {subcommunity_id}, handle: {subcommunity_handle}): {subcommunity_name} ==> I must go deeper!\n".format(
                        subcommunity_id=str(subcommunity_id),
                        subcommunity_handle=subcommunity["handle"],
                        subcommunity_name=subcommunity["name"],
                    )
                    + Fore.RESET
                )

            parse_community(subcommunity_id)

        for collection in collections:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + "Found collection (id: {collection_id}, handle: {collection_handle}): {collection_name}\n".format(
                        collection_id=str(collection["uuid"]),
                        collection_handle=collection["handle"],
                        collection_name=collection["name"],
                    )
                    + Fore.RESET
                )

            all_collections.append(collection["name"])
    else:
        sys.stderr.write(
            Fore.RED
            + "Status not ok! Request URL was: {request_url}\n".format(
                request_url=request.url
            )
            + Fore.RESET
        )
        exit(1)


parser = argparse.ArgumentParser(
    description="Find all collections under a given DSpace community."
)
parser.add_argument("community", help="Community to process, for example: 10568/1")
parser.add_argument("-d", "--debug", help="Print debug messages.", action="store_true")
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

# initialize empty list of all collections
all_collections = []

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# fetch the metadata for the given handle
request_url = rest_base_url + rest_handle_endpoint + str(handle)

try:
    request = requests.get(request_url, headers={"user-agent": rest_user_agent})
except requests.ConnectionError:
    sys.stderr.write(
        Fore.RED
        + "Could not connect to REST API: {0}.\n".format(args.rest_url)
        + Fore.RESET
    )
    exit(1)

# Check the request status
if request.status_code == requests.codes.ok:
    handle_type = request.json()["type"]

    # Make sure the given handle is a community
    if handle_type == "community":
        community_id = request.json()["uuid"]
        parse_community(community_id)

        for collection in all_collections:
            print(
                Fore.GREEN
                + "Name of collection: {collection}".format(collection=collection)
                + Fore.RESET
            )
    else:
        sys.stderr.write(
            Fore.RED
            + '{handle} is type "{handle_type}", not community.\n'.format(
                handle=handle, handle_type=handle_type
            )
            + Fore.RESET
        )
        exit(1)
else:
    sys.stderr.write(
        Fore.RED
        + "Request failed. Are you sure {handle} is a valid handle?\n".format(
            handle=handle
        )
        + Fore.RESET
    )
    exit(1)
