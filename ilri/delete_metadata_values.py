#!/usr/bin/env python3
#
# delete-metadata-values.py 1.2.5
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Expects a CSV with one column of metadata values to delete, for example:
#
# cg.contributor.affiliation
# "some value to delete"
#
#   $ ./delete-metadata-values.py -db database -u user -p password -f cg.contributor.affiliation -i file.csv
#
# This script is written for Python 3 and DSpace 6+ and requires several modules
# that you can install with pip (I recommend setting up a Python virtual env
# first):
#
#   $ pip install psycopg colorama
#

import argparse
import csv
import signal
import sys

import util
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(0)


parser = argparse.ArgumentParser(
    description="Delete metadata values in the DSpace SQL database."
)
parser.add_argument(
    "-i",
    "--csv-file",
    help="Path to CSV file",
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
    help="Name of column with values to be deleted",
    required=True,
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
args = parser.parse_args()

# open the CSV
reader = csv.DictReader(args.csv_file)

# check if the from/to fields specified by the user exist in the CSV
if args.from_field_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + 'Specified field "{0}" does not exist in the CSV.\n'.format(
            args.from_field_name
        )
        + Fore.RESET
    )
    sys.exit(1)

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
conn = util.db_connect(
    args.database_name, args.database_user, args.database_pass, "localhost"
)

if args.dry_run:
    conn.read_only = True

cursor = conn.cursor()

for row in reader:
    metadata_field_id = util.field_name_to_field_id(cursor, args.from_field_name)

    # Get item UUIDs for metadata values that will be updated
    sql = "SELECT dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
    cursor.execute(sql, (metadata_field_id, row[args.from_field_name]))

    if cursor.rowcount > 0:
        if args.dry_run:
            if not args.quiet:
                print(
                    Fore.GREEN
                    + "Would delete {0} occurences of: {1}".format(
                        cursor.rowcount, row[args.from_field_name]
                    )
                    + Fore.RESET
                )

            # Since this a dry run we can continue to the next replacement
            continue

        # Get the records for items with matching metadata. We will use the
        # object IDs to update their last_modified dates.
        matching_records = cursor.fetchall()

        sql = "DELETE from metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
        cursor.execute(sql, (metadata_field_id, row[args.from_field_name]))

        if cursor.rowcount > 0 and not args.quiet:
            print(
                Fore.GREEN
                + "Deleted {0} occurences of: {1}".format(
                    cursor.rowcount, row[args.from_field_name]
                )
                + Fore.RESET
            )

        # Update the last_modified date for each item we've changed
        for record in matching_records:
            util.update_item_last_modified(cursor, record[0])


# commit the changes when we are done
if not args.dry_run:
    conn.commit()

# close database connection before we exit
conn.close()

# close the input file
args.csv_file.close()

sys.exit(0)
