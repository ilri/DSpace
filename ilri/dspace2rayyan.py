#!/usr/bin/env python3
#
# dspace2rayyan.py 0.0.2
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
    "Authors": ["dc.contributor.author", "dc.creator", "dc.contributor"],
    "Author affiliations": ["cg.contributor.affiliation", "cg.contributor.center"],
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
    ],
    "Usage rights": ["dcterms.license", "dc.rights"],
    "URL": [],  # this comes from DSpace's item.handle
    "Year": ["dcterms.issued", "dc.date.issued", "dcterms.available"],
    "Journal": ["cg.journal", "dc.source", "dc.source.title", "dc.source.journal"],
    "ISSN": ["cg.issn", "dc.identifier.issn", "dc.source.issn"],
    "Publisher": ["dcterms.publisher", "dc.publisher"],
    "Volume": ["cg.volume", "dc.source.volume"],
    "Issue": ["cg.issue", "dc.source.issue"],
    "Pages": ["dcterms.extent", "dc.description.pages"],
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

    # Use a list instead of None here because an empty list is Falsy as well and
    # we need an iterable to be able to join later when serializing to CSV.
    item_authors = []
    for field in field_mappings["Authors"]:
        logger.debug(f"Trying to find authors in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_authors = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                pass

        if item_authors:
            break

    item_affiliations = []
    for field in field_mappings["Author affiliations"]:
        logger.debug(f"Trying to find author affiliations in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_affiliations = [
                    k["value"] for k in item.get_metadata_values(field)
                ]
            except IndexError:
                pass

        if item_affiliations:
            break

    item_abstract = None
    for field in field_mappings["Abstract"]:
        logger.debug(f"Trying to find abstract in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_abstract = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_abstract = None

        if item_abstract:
            break

    item_language = None
    for field in field_mappings["Language"]:
        logger.debug(f"Trying to find language in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_language = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_language = None

        if item_language:
            break

    item_doi = None
    for field in field_mappings["DOI"]:
        logger.debug(f"Trying to find DOI in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_doi = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_doi = None

        if item_doi:
            break

    item_access_rights = None
    for field in field_mappings["Access rights"]:
        logger.debug(f"Trying to find access rights in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_access_rights = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_access_rights = None

        if item_access_rights:
            break

    item_usage_rights = None
    for field in field_mappings["Usage rights"]:
        logger.debug(f"Trying to find usage rights in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_usage_rights = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_usage_rights = None

        if item_usage_rights:
            break

    item_date_issued = None
    for field in field_mappings["Year"]:
        logger.debug(f"Trying to find date issued in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_date_issued = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_date_issued = None

        if item_date_issued:
            break

    if not item_date_issued:
        logger.error(f"Missing date. This shouldn't happen! {item.handle} ({item.id})")

        sys.exit(1)

    # Truncate to YYYY for Rayyan
    try:
        item_date_issued = item_date_issued[0:4]
    except AttributeError:
        logger.error(f"Malformed date. This shouldn't happen! {item.handle}")

        sys.exit(1)

    item_journal = None
    for field in field_mappings["Journal"]:
        logger.debug(f"Trying to find journal in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_journal = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_journal = None

        if item_journal:
            break

    item_issn = []
    for field in field_mappings["ISSN"]:
        logger.debug(f"Trying to find ISSN in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_issn = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                item_issn = []

        if item_issn:
            break

    item_publisher = []
    for field in field_mappings["Publisher"]:
        logger.debug(f"Trying to find publisher in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_publisher = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                item_publisher = []

        if item_publisher:
            break

    item_volume = None
    for field in field_mappings["Volume"]:
        logger.debug(f"Trying to find volume in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_volume = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_volume = None

        if item_volume:
            break

    item_issue = None
    for field in field_mappings["Issue"]:
        logger.debug(f"Trying to find issue in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_issue = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_issue = None

        if item_issue:
            break

    item_extent = None
    for field in field_mappings["Pages"]:
        logger.debug(f"Trying to find pages in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_extent = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_extent = None

        if item_extent:
            break

    item_type = None
    for field in field_mappings["Type"]:
        logger.debug(f"Trying to find type in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_type = item.get_metadata_values(field)[0]["value"]
            except IndexError:
                item_type = None

        if item_type:
            break

    if not item_type:
        logger.error(f"Missing type. This shouldn't happen! {item.handle}")

    item_funders = []
    for field in field_mappings["Funders"]:
        logger.debug(f"Trying to find funders in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_funders = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                item_funders = []

        if item_funders:
            break

    item_subjects = []
    for field in field_mappings["Keywords"]:
        logger.debug(f"Trying to find keywords in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_subjects = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                item_subjects = []

        if item_subjects:
            break

    item_countries = []
    for field in field_mappings["Countries"]:
        logger.debug(f"Trying to find countries in {field}")

        if len(item.get_metadata_values(field)) > 0:
            try:
                item_countries = [k["value"] for k in item.get_metadata_values(field)]
            except IndexError:
                item_countries = []

        if item_countries:
            break

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
