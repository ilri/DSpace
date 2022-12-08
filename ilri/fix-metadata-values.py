#!/usr/bin/env python3
#
# fix-metadata-values.py v1.2.1
#
# Copyright 2018–2022 Alan Orth
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
#   $ pip install psycopg2 colorama
#
# See: http://initd.org/psycopg
# See: http://initd.org/psycopg/docs/usage.html#with-statement
# See: http://initd.org/psycopg/docs/faq.html#best-practices
#
# TODO:
#   - look up metadata field IDs automatically

import argparse
import csv
import signal
import sys

import psycopg2
import util
from colorama import Fore


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
    "-m",
    "--metadata-field-id",
    type=int,
    help="ID of the field in the metadatafieldregistry table.",
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

# open the CSV
reader = csv.DictReader(args.csv_file)

# check if the from/to fields specified by the user exist in the CSV
if args.from_field_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'Specified field "{args.from_field_name}" does not exist in the CSV.\n'
        + Fore.RESET
    )
    sys.exit(1)
if args.to_field_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'Specified field "{args.to_field_name}" does not exist in the CSV.\n'
        + Fore.RESET
    )
    sys.exit(1)

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg2.connect(
        f"dbname={args.database_name} user={args.database_user} password={args.database_pass} host='localhost'"
    )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Connected to database.\n" + Fore.RESET)
except psycopg2.OperationalError:
    sys.stderr.write(Fore.RED + "Could not connect to database.\n" + Fore.RESET)
    sys.exit(1)

for row in reader:
    if row[args.from_field_name] == row[args.to_field_name]:
        if args.debug:
            # sometimes editors send me corrections with identical search/replace patterns
            sys.stderr.write(
                Fore.YELLOW
                + f"Skipping identical search and replace for value: {row[args.from_field_name]}\n"
                + Fore.RESET
            )

        continue

    if "|" in row[args.to_field_name]:
        if args.debug:
            # sometimes editors send me corrections with multi-value fields, which are supported in DSpace itself, but not here!
            sys.stderr.write(
                Fore.YELLOW
                + f"Skipping correction with invalid | character: {row[args.to_field_name]}\n"
                + Fore.RESET
            )

        continue

    with conn:
        # cursor will be closed after this block exits
        # see: http://initd.org/psycopg/docs/usage.html#with-statement
        with conn.cursor() as cursor:
            # Get item UUIDs for metadata values that will be updated
            sql = "SELECT dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item) AND metadata_field_id=%s AND text_value=%s"
            cursor.execute(sql, (args.metadata_field_id, row[args.from_field_name]))

            if cursor.rowcount > 0:
                if args.dry_run:
                    if not args.quiet:
                        print(
                            Fore.GREEN
                            + f"Would fix {cursor.rowcount} occurences of: {row[args.from_field_name]}"
                            + Fore.RESET
                        )

                    # Since this a dry run we can continue to the next replacement
                    continue

                # Get the records for items with matching metadata. We will use the
                # object IDs to update their last_modified dates.
                matching_records = cursor.fetchall()

                sql = "UPDATE metadatavalue SET text_value=%s WHERE dspace_object_id IN (SELECT uuid FROM item) AND metadata_field_id=%s AND text_value=%s"
                cursor.execute(
                    sql,
                    (
                        row[args.to_field_name],
                        args.metadata_field_id,
                        row[args.from_field_name],
                    ),
                )

                if cursor.rowcount > 0 and not args.quiet:
                    print(
                        Fore.GREEN
                        + f"Fixed {cursor.rowcount} occurences of: {row[args.from_field_name]}"
                        + Fore.RESET
                    )

                # Update the last_modified date for each item we've changed
                for record in matching_records:
                    util.update_item_last_modified(cursor, record[0])


# close database connection before we exit
conn.close()

# close input file
args.csv_file.close()

sys.exit(0)
