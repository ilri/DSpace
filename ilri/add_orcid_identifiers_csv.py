#!/usr/bin/env python3
#
# add-orcid-identifiers-csv.py v1.1.6
#
# Copyright Alan Orth.

# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Add ORCID identifiers to items for a given author name from CSV.
#
# We had previously migrated the ORCID identifiers from CGSpace's authority Solr
# core to cg.creator.identifier fields in matching items, but now we want to add
# them to # other matching items in a more arbitrary fashion. Items that are ol-
# der or were uploaded in batch did not have matching authors in the authority
# core, so they did not benefit from that migration, for example.
#
# This script searches for items by author name and adds a cg.creator.identifier
# field to each (assuming one does not exist). The format of the CSV file should
# be:
#
# dc.contributor.author,cg.creator.identifier
# "Orth, Alan",Alan S. Orth: 0000-0002-1735-7458
# "Orth, A.",Alan S. Orth: 0000-0002-1735-7458
#
# The order of authors in dc.contributor.author is respected and mirrored in the
# new cg.creator.identifier fields.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama
#

import argparse
import csv
import logging
import re
import signal
import sys

import util
from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser(
        description="Add ORCID identifiers to items for a given author name from CSV. Respects the author order from the dc.contributor.author field."
    )
    parser.add_argument(
        "--author-field-name",
        "-f",
        help="Name of column with author names.",
        default="dc.contributor.author",
    )
    parser.add_argument(
        "--csv-file",
        "-i",
        help="CSV file containing author names and ORCID identifiers.",
        required=True,
        type=argparse.FileType("r", encoding="UTF-8"),
    )
    parser.add_argument("--database-name", "-db", help="Database name", required=True)
    parser.add_argument(
        "--database-user", "-u", help="Database username", required=True
    )
    parser.add_argument(
        "--database-pass", "-p", help="Database password", required=True
    )
    parser.add_argument(
        "--debug",
        "-d",
        help="Print debug messages to standard error (stderr).",
        action="store_true",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        help="Only print changes that would be made.",
        action="store_true",
    )
    parser.add_argument(
        "--orcid-field-name",
        "-o",
        help='Name of column with creators in "Name: 0000-0000-0000-0000" format.',
        default="cg.creator.identifier",
    )
    args = parser.parse_args()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set the global log format
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    # set the signal handler for SIGINT (^C) so we can exit cleanly
    signal.signal(signal.SIGINT, signal_handler)

    # connect to database
    conn = util.db_connect(
        args.database_name, args.database_user, args.database_pass, "localhost"
    )

    cursor = conn.cursor()

    # open the CSV
    reader = csv.DictReader(args.csv_file)

    # iterate over rows in the CSV
    for row in reader:
        author_name = row[args.author_field_name]

        logger.debug(
            Fore.GREEN + f"Finding items with author name: {author_name}" + Fore.RESET
        )

        # find all item metadata records with this author name
        # metadata_field_id 3 is author
        sql = "SELECT dspace_object_id, place FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=3 AND text_value=%s"
        # remember that tuples with one item need a comma after them!
        cursor.execute(sql, (author_name,))
        records_with_author_name = cursor.fetchall()

        if len(records_with_author_name) > 0:
            logger.debug(
                Fore.GREEN
                + f"> Found {len(records_with_author_name)} items."
                + Fore.RESET
            )

            # extract cg.creator.identifier text to add from CSV and strip leading/trailing whitespace
            text_value = row[args.orcid_field_name].strip()
            # extract the ORCID identifier from the cg.creator.identifier text field in the CSV
            orcid_identifier_pattern = re.compile(
                r"[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}"
            )
            orcid_identifier_match = orcid_identifier_pattern.search(text_value)

            # sanity check to make sure we extracted the ORCID identifier from the cg.creator.identifier text in the CSV
            if orcid_identifier_match is None:
                logger.debug(
                    Fore.YELLOW
                    + f'Skipping invalid ORCID identifier in "{text_value}".'
                    + Fore.RESET
                )
                continue

            # we only expect one ORCID identifier, so if it matches it will be group "0"
            # see: https://docs.python.org/3/library/re.html
            orcid_identifier = orcid_identifier_match.group(0)

            # iterate over results for current author name to add cg.creator.identifier metadata
            for record in records_with_author_name:
                dspace_object_id = record[0]
                # "place" is the order of a metadata value so we can add the cg.creator.identifier metadata matching the author order
                place = record[1]
                confidence = -1

                # get the metadata_field_id for the cg.creator.identifier field
                metadata_field_id = util.field_name_to_field_id(
                    cursor, "cg.creator.identifier"
                )

                # check if there is an existing cg.creator.identifier with this author's ORCID identifier for this item (without restricting the "place")
                # note that the SQL here is quoted differently to allow us to use LIKE with % wildcards with our paremeter subsitution
                sql = "SELECT * from metadatavalue WHERE dspace_object_id=%s AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND confidence=%s AND dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn)"

                cursor.execute(
                    sql,
                    (
                        dspace_object_id,
                        metadata_field_id,
                        orcid_identifier,
                        confidence,
                    ),
                )
                records_with_orcid_identifier = cursor.fetchall()

                if len(records_with_orcid_identifier) == 0:
                    if args.dry_run:
                        logger.info(
                            Fore.YELLOW
                            + f'(DRY RUN) Adding ORCID identifier "{text_value}" to item {dspace_object_id}'
                            + Fore.RESET
                        )

                        continue

                    logger.info(
                        Fore.YELLOW
                        + f'Adding ORCID identifier "{text_value}" to item {dspace_object_id}'
                        + Fore.RESET
                    )

                    # metadatavalue IDs come from a PostgreSQL sequence that increments when you call it
                    cursor.execute("SELECT nextval('metadatavalue_seq')")
                    metadata_value_id = cursor.fetchone()[0]

                    sql = "INSERT INTO metadatavalue (metadata_value_id, dspace_object_id, metadata_field_id, text_value, place, confidence) VALUES (%s, %s, %s, %s, %s, %s)"
                    cursor.execute(
                        sql,
                        (
                            metadata_value_id,
                            dspace_object_id,
                            metadata_field_id,
                            text_value,
                            place,
                            confidence,
                        ),
                    )

                    # Update the last_modified date for each item
                    util.update_item_last_modified(cursor, dspace_object_id)
                else:
                    logger.debug(
                        Fore.GREEN
                        + f"Item {dspace_object_id} already has an ORCID identifier for {text_value}."
                        + Fore.RESET
                    )

    logger.debug("Disconnecting from database.")

    # commit the changes
    if not args.dry_run:
        conn.commit()

    # close the database connection before leaving
    conn.close()

    # close output file before we exit
    args.csv_file.close()


def signal_handler(signal, frame):
    sys.exit(1)


if __name__ == "__main__":
    main()
