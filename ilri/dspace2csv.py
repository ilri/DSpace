#!/usr/bin/env python3
#
# dspace2csv.py v0.0.3
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the DSpace 7+ API for items matching search results and writes to CSV.
#
# TODO:
#   - fetch collections
import argparse
import csv
import logging
import signal
import sys
from datetime import timedelta

import requests_cache
from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Item

# Create a local logger instance
logger = logging.getLogger(__name__)

requests_cache.install_cache(
    "harvest-cache", expire_after=timedelta(days=30), allowable_codes=[200]
)

# prune old cache entries
requests_cache.delete(expired=True)


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Harvest items from a DSpace repository using the DSpace 7+ REST API."
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print debug messages to standard error (stderr).",
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--fields",
        required=True,
        help="Comma-separated list of fields to include in export, for example: dc.title,dc.contributor.author,dcterms.bibliographicCitation",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="File to write results to (CSV).",
        required=True,
        type=argparse.FileType("w", encoding="UTF-8"),
    )
    parser.add_argument(
        "--scope",
        required=False,
        help="Community or collection scope (UUID).",
    )
    parser.add_argument(
        "-s",
        "--search-string",
        required=True,
        help="Search string. See: https://wiki.lyrasis.org/display/DSDOC8x/Search+-+Advanced",
    )
    parser.add_argument(
        "-u",
        "--api-url",
        required=True,
        help="The API URL.",
        default="https://demo.dspace.org/server/api",
    )
    args = parser.parse_args()

    return args


def main(args):
    d = DSpaceClient(api_endpoint=args.api_url)

    logger.debug(f"Connected to {args.api_url}")

    # Prepare the CSV header based on the user's list of metadata fields plus the
    # item's ID, ignoring the ID field if the user specified it because we always
    # want it.
    fields = ["id"] + [field for field in args.fields.split(",") if field != "id"]
    writer = csv.DictWriter(args.output_file, fieldnames=fields)
    writer.writeheader()

    logger.debug(f"Opened output file {args.output_file.name}")

    item_number = 1
    for item in d.search_objects_iter(
        dso_type="item", scope=args.scope, query=args.search_string
    ):
        item = Item.from_dso(item)

        # Initialize empty dict to start building our row of item metadata
        row = dict()

        # Add the ID first
        row["id"] = item.uuid

        # Iterate over user-specified fields and extract matching metadata
        # from the item. Join multiple values with "; ".
        for field in fields[1:]:
            # DSpace Python client always returns a list, even if the metadata
            # does not exist. We need to make sure the list is populated.
            if len(item.get_metadata_values(field)) > 0:
                metadatum = [
                    metadatum["value"] for metadatum in item.get_metadata_values(field)
                ]

                # Don't use multiple values for date fields, e.g. dc.date.issued
                # or dcterms.issued, or dcterms.available. Instead, if the field
                # is a date and has multiple values, only take the first!
                if "issued" in field or "available" in field:
                    row[field] = metadatum[0]
                else:
                    row[field] = "; ".join(metadatum)

        writer.writerow(row)

        logger.debug(f"Wrote item {item_number}")
        item_number += 1

    # close output file before we exit
    args.output_file.close()

    logger.debug(f"Closed output file {args.output_file.name}")


if __name__ == "__main__":
    args = parse_arguments()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set the global log format since we are running interactively
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    # set the signal handler for SIGINT (^C) so we can exit cleanly
    signal.signal(signal.SIGINT, signal_handler)

    main(args)
