#!/usr/bin/env python3
#
# dspace2rayyan.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the DSpace 7+ API for items matching search results and writes to CSV.
#

import argparse
import csv
import logging
import sys
from datetime import timedelta

import requests_cache
from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Item

requests_cache.install_cache(
    "harvest-cache", expire_after=timedelta(days=30), allowable_codes=(200, 404)
)

# prune old cache entries
requests_cache.delete(expired=True)

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", help="Print debug output.")
parser.add_argument(
    "-o",
    "--output-file",
    help="File name to save CSV output.",
    required=True,
    type=argparse.FileType("w"),
)
parser.add_argument(
    "-s",
    "--search-string",
    required=True,
    help="Search string. See: https://wiki.lyrasis.org/display/DSDOC7x/Search+-+Advanced",
)
parser.add_argument(
    "-u",
    "--api-url",
    required=True,
    help="The API URL.",
    default="https://demo.dspace.org/server/api",
)

args = parser.parse_args()

# Create a local logger instance
logger = logging.getLogger(__name__)

# The default log level is WARNING, but we want to set it to DEBUG or INFO
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

d = DSpaceClient(api_endpoint=args.api_url)

fieldnames = [
    "Title",
    "Authors",
    "Author affiliations",
    "Abstract",
    "Funders",
    "Language",
    "DOI",
    "Access rights",
    "Usage rights",
    "URL",
    "Year",
    "Journal",
    "ISSN",
    "Publisher",
    "Volume",
    "Issue",
    "Pages",
    "Type",
    "Keywords",
    "Countries",
]

writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
writer.writeheader()

item_number = 0
for item in d.search_objects_iter(dso_type="item", query=args.search_string):
    item = Item.from_dso(item)

    try:
        item_authors = [
            k["value"] for k in item.get_metadata_values("dc.contributor.author")
        ]
    except IndexError:
        item_authors = None

    try:
        item_affiliations = [
            k["value"] for k in item.get_metadata_values("cg.contributor.affiliation")
        ]
    except IndexError:
        item_affiliations = None

    try:
        item_abstract = item.get_metadata_values("dcterms.abstract")[0]["value"]
    except IndexError:
        item_abstract = None

    try:
        item_language = item.get_metadata_values("dcterms.language")[0]["value"]
    except IndexError:
        item_language = None

    try:
        item_doi = item.get_metadata_values("cg.identifier.doi")[0]["value"]
    except IndexError:
        item_doi = None

    try:
        item_access_rights = item.get_metadata_values("dcterms.accessRights")[0][
            "value"
        ]
    except IndexError:
        item_access_rights = None

    try:
        item_usage_rights = item.get_metadata_values("dcterms.license")[0]["value"]
    except IndexError:
        item_usage_rights = None

    # Try to get either the issue date or online date
    try:
        item_date_issued = item.get_metadata_values("dcterms.issued")[0]["value"]
    except IndexError:
        try:
            item_date_issued = item.get_metadata_values("dcterms.available")[0]["value"]
        except IndexError:
            logger.error(
                f"Missing date. This shouldn't happen! {item.handle} ({item.id})"
            )

            sys.exit(1)

    # Truncate to YYYY for Rayyan
    try:
        item_date_issued = item_date_issued[0:4]
    except AttributeError:
        logger.error(f"Malformed date. This shouldn't happen! {item.handle}")

        sys.exit(1)

    try:
        item_journal = item.get_metadata_values("cg.journal")[0]["value"]
    except IndexError:
        item_journal = None

    try:
        item_issn = item.get_metadata_values("cg.issn")[0]["value"]
    except IndexError:
        item_issn = None

    # TODO: this could be multiple values for some items
    try:
        item_publisher = item.get_metadata_values("dcterms.publisher")[0]["value"]
    except IndexError:
        item_publisher = None

    try:
        item_volume = item.get_metadata_values("cg.volume")[0]["value"]
    except IndexError:
        item_volume = None

    try:
        item_issue = item.get_metadata_values("cg.issue")[0]["value"]
    except IndexError:
        item_issue = None

    try:
        item_extent = item.get_metadata_values("dcterms.extent")[0]["value"]
    except IndexError:
        item_extent = None

    try:
        item_type = item.get_metadata_values("dcterms.type")[0]["value"]
    except IndexError:
        logger.error(f"Missing type. This shouldn't happen! {item.handle}")

        item_type = None

    try:
        item_funders = [
            k["value"] for k in item.get_metadata_values("cg.contributor.donor")
        ]
    except IndexError:
        item_funders = None

    try:
        item_subjects = [
            k["value"] for k in item.get_metadata_values("dcterms.subject")
        ]
    except IndexError:
        item_subjects = None

    try:
        item_countries = [
            k["value"] for k in item.get_metadata_values("cg.coverage.country")
        ]
    except IndexError:
        item_countries = None

    writer.writerow(
        {
            "Title": item.name,
            "Authors": "; ".join(item_authors),
            "Author affiliations": "; ".join(item_affiliations),
            "Abstract": item_abstract,
            "Language": item_language,
            "DOI": item_doi,
            "Access rights": item_access_rights,
            "Usage rights": item_usage_rights,
            "URL": f"https://hdl.handle.net/{item.handle}",
            "Year": item_date_issued,
            "Journal": item_journal,
            "ISSN": item_issn,
            "Publisher": item_publisher,
            "Volume": item_volume,
            "Issue": item_issue,
            "Pages": item_extent,
            "Type": item_type,
            "Funders": "; ".join(item_funders),
            "Keywords": "; ".join(item_subjects),
            "Countries": "; ".join(item_countries),
        }
    )

    logger.debug(f"Wrote item {item_number}")
    item_number += 1

logger.info(f"Wrote {args.output_file.name}")

# close output file before we exit
args.output_file.close()
