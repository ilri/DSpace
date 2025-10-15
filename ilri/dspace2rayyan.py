#!/usr/bin/env python3
#
# dspace2rayyan.py 0.2.0
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
from util import normalize_cgiar_affiliations, normalize_doi


def get_metadata_value_list(item_dso, fields: list) -> list:
    """Get multi-value metadata from an item. Use this when the metadata you are
    getting is logically more than one thing. For example: authors or ISSNs.

    :param item_dso: a dspace_rest_client Item object.
    :param fields: a list of metadata fields to look up (in order, first one wins).
    :returns list
    """

    # Use a list instead of None here because an empty list is Falsy as well and
    # we need an iterable to be able to join later when serializing to CSV.
    item_metadata_values = []
    for field in fields:
        if len(item.get_metadata_values(field)) > 0:
            try:
                item_metadata_values = [
                    k["value"].strip() for k in item.get_metadata_values(field)
                ]
            except IndexError:
                item_metadata_values = []

        if item_metadata_values:
            break

    return item_metadata_values


def get_metadata_value_string(item_dso, fields: list) -> str:
    """Get single metadata value from an item. Use this when the metadata you are
    getting is logically only one thing. For example: title or DOI.

    :param item_dso: a dspace_rest_client Item object.
    :param fields: a list of metadata fields to look up (in order, first one wins).
    :returns list
    """
    item_metadata_value = None
    for field in fields:
        if len(item.get_metadata_values(field)) > 0:
            try:
                item_metadata_value = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_metadata_value = None

        if item_metadata_value:
            break

    return item_metadata_value


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
    "--scope",
    required=False,
    help="Community or collection scope (UUID).",
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

field_mappings = {
    "Title": [],  # this comes from DSpace's item.name
    # Unfortunately MELSpace will need a custom harvester because they use one field
    # for the first author, and another for the rest.
    "Authors": [
        "dc.contributor.author",
        "dc.creator",
        "dc.contributor",
        "dc.creator.corporate",  # CIMMYT
    ],
    "Author affiliations": [
        "cg.contributor.affiliation",
        "cg.contributor.center",
        "dc.creator.corporate",  # CIMMYT
    ],
    # Try in order of liklihood (CIMMYT uses all of these, sigh...)
    "Abstract": ["dcterms.abstract", "dc.description.abstract", "dc.description"],
    "Funders": [
        "cg.contributor.donor",
        "cg.contributor.funder",
        "dc.relation.funderName",
    ],
    "Language": ["dcterms.language", "dc.language.iso", "dc.language"],
    "DOI": ["cg.identifier.doi", "dc.identifier.doi"],
    "Access rights": [
        "dcterms.accessRights",
        "dc.identifier.status",
        "dc.rights.accesslevel",
        "cg.identifier.status", # WorldFish
    ],
    "Usage rights": ["dcterms.license", "dc.rights"],
    "URL": [],  # this comes from DSpace's item.handle
    "Year": ["dcterms.issued", "dc.date.issued", "dcterms.available"],
    "Journal": ["cg.journal", "dc.source", "dc.source.title", "dc.source.journal"],
    "ISSN": ["cg.issn", "dc.identifier.issn", "dc.source.issn"],
    "Publisher": ["dcterms.publisher", "dc.publisher", "dc.publisher.name"],
    "Volume": ["cg.volume", "dc.source.volume"],
    "Issue": ["cg.issue", "dc.source.issue"],
    "Pages": ["dcterms.extent", "dc.description.pages", "dc.source.page"],
    "Type": ["dcterms.type", "dc.type"],
    "Keywords": [
        "dcterms.subject",
        "dc.subject",
        "cg.subject.agrovoc",
        "dc.subject.agrovoc",
        "dc.subject.other",
    ],
    "Countries": ["cg.coverage.country", "dc.coverage.countryfocus"],
}

field_names = [field for field in field_mappings]

writer = csv.DictWriter(args.output_file, fieldnames=field_names)
writer.writeheader()

item_number = 0
for item in d.search_objects_iter(
    dso_type="item", scope=args.scope, query=args.search_string
):
    item = Item.from_dso(item)

    item_authors = normalize_cgiar_affiliations(
        get_metadata_value_list(item, field_mappings["Authors"])
    )
    item_affiliations = normalize_cgiar_affiliations(
        get_metadata_value_list(item, field_mappings["Author affiliations"])
    )
    item_abstract = get_metadata_value_string(item, field_mappings["Abstract"])
    item_language = get_metadata_value_string(item, field_mappings["Language"])
    item_doi = normalize_doi(get_metadata_value_string(item, field_mappings["DOI"]))
    item_access_rights = get_metadata_value_string(
        item, field_mappings["Access rights"]
    )
    item_usage_rights = get_metadata_value_string(item, field_mappings["Usage rights"])
    item_date_issued = get_metadata_value_string(item, field_mappings["Year"])

    if not item_date_issued:
        logger.error(f"Missing date. This shouldn't happen! {item.handle} ({item.id})")

        sys.exit(1)

    # Strip some weird characters from some dates like "[2014]" I've seen in one
    # repository and truncate to YYYY for Rayyan.
    try:
        item_date_issued = item_date_issued.strip("[]")[0:4]
    except AttributeError:
        logger.error(f"Malformed date. This shouldn't happen! {item.handle}")

        sys.exit(1)

    item_journal = get_metadata_value_string(item, field_mappings["Journal"])
    item_issn = get_metadata_value_list(item, field_mappings["ISSN"])
    item_publisher = normalize_cgiar_affiliations(
        get_metadata_value_list(item, field_mappings["Publisher"])
    )
    item_volume = get_metadata_value_string(item, field_mappings["Volume"])
    item_issue = get_metadata_value_string(item, field_mappings["Issue"])
    item_extent = get_metadata_value_string(item, field_mappings["Pages"])
    item_type = get_metadata_value_string(item, field_mappings["Type"])

    if not item_type:
        logger.error(f"Missing type. This shouldn't happen! {item.handle}")

    item_funders = normalize_cgiar_affiliations(
        get_metadata_value_list(item, field_mappings["Funders"])
    )
    item_subjects = get_metadata_value_list(item, field_mappings["Keywords"])
    item_countries = get_metadata_value_list(item, field_mappings["Countries"])

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
            "ISSN": "; ".join(item_issn),
            "Publisher": "; ".join(item_publisher),
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
