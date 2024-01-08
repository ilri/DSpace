#!/usr/bin/env python3
#
# fix-metadata-values.py v1.2.6
#
# Copyright Alan Orth
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Expects a CSV with two columns: one with "bad" metadata values and one with
# correct values. Basically just a mass search and replace function for DSpace's
# PostgreSQL database. This script only works on DSpace 6+. Make sure to do a
# full `index-discovery -b` afterwards.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install psycopg colorama
#
# See: https://www.psycopg.org/psycopg3/docs
#

import argparse
import csv
import logging
import signal
import sys

import util
from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Find and replace metadata values in the DSpace SQL database."
)
parser.add_argument(
    "-i",
    "--csv-file",
    help="Path to CSV file",
    required=True,
    type=argparse.FileType("r", encoding="UTF-8"),
)
parser.add_argument("-db", "--database-name", help="Database name", required=True)
parser.add_argument("-u", "--database-user", help="Database username", required=True)
parser.add_argument("-p", "--database-pass", help="Database password", required=True)
parser.add_argument(
    "-d",
    "--debug",
    help="Print debug messages to standard error (stderr).",
    action="store_true",
)
parser.add_argument(
    "-n",
    "--dry-run",
    help="Only print changes that would be made.",
    action="store_true",
)
parser.add_argument(
    "-f",
    "--from-field-name",
    help="Name of column with values to be replaced.",
    required=True,
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
parser.add_argument(
    "-t",
    "--to-field-name",
    help="Name of column with values to replace.",
    required=True,
)
args = parser.parse_args()

# The default log level is WARNING, but we want to set it to DEBUG or INFO
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Set the global log format
logging.basicConfig(format="[%(levelname)s] %(message)s")

# open the CSV
reader = csv.DictReader(args.csv_file)

# check if the from/to fields specified by the user exist in the CSV
if args.from_field_name not in reader.fieldnames:
    logger.error(
        Fore.RED
        + f'Specified field "{args.from_field_name}" does not exist in the CSV.'
        + Fore.RESET
    )
    sys.exit(1)
if args.to_field_name not in reader.fieldnames:
    logger.error(
        Fore.RED
        + f'Specified field "{args.to_field_name}" does not exist in the CSV.'
        + Fore.RESET
    )
    sys.exit(1)

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
conn = util.db_connect(
    args.database_name, args.database_user, args.database_pass, "localhost"
)

cursor = conn.cursor()

for row in reader:
    if row[args.from_field_name] == row[args.to_field_name]:
        # sometimes editors send me corrections with identical search/replace patterns
        logger.debug(
            Fore.YELLOW
            + f"Skipping identical search and replace for value: {row[args.from_field_name]}"
            + Fore.RESET
        )

        continue

    if "|" in row[args.to_field_name]:
        # sometimes editors send me corrections with multi-value fields, which are supported in DSpace itself, but not here!
        logger.debug(
            Fore.YELLOW
            + f"Skipping correction with invalid | character: {row[args.to_field_name]}"
            + Fore.RESET
        )

        continue

    metadata_field_id = util.field_name_to_field_id(cursor, args.from_field_name)

    # Get item UUIDs for metadata values that will be updated
    sql = "SELECT dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
    cursor.execute(sql, (metadata_field_id, row[args.from_field_name]))

    if cursor.rowcount > 0:
        if args.dry_run:
            if not args.quiet:
                logger.info(
                    Fore.GREEN
                    + f"(DRY RUN) Fixed {cursor.rowcount} occurences of: {row[args.from_field_name]}"
                    + Fore.RESET
                )

            # Since this a dry run we can continue to the next replacement
            continue

        # Get the records for items with matching metadata. We will use the
        # object IDs to update their last_modified dates.
        matching_records = cursor.fetchall()

        sql = "UPDATE metadatavalue SET text_value=%s WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
        cursor.execute(
            sql,
            (
                row[args.to_field_name],
                metadata_field_id,
                row[args.from_field_name],
            ),
        )

        if cursor.rowcount > 0 and not args.quiet:
            logger.info(
                Fore.GREEN
                + f"Fixed {cursor.rowcount} occurences of: {row[args.from_field_name]}"
                + Fore.RESET
            )

        # Update the last_modified date for each item we've changed
        for record in matching_records:
            util.update_item_last_modified(cursor, record[0])


# commit changes after we are done
if not args.dry_run:
    conn.commit()

# close database connection before we exit
conn.close()

# close input file
args.csv_file.close()

sys.exit(0)
