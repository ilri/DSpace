#!/usr/bin/env python3

# move-metadata-values.py 0.1.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Expects a text with one metadata value per line. The idea is to move some
# matching metadatavalues from one field to another, rather than moving all
# metadata values (as in the case of migrate-fields.sh).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install psycopg2 colorama
#
# See: http://initd.org/psycopg
# See: http://initd.org/psycopg/docs/usage.html#with-statement
# See: http://initd.org/psycopg/docs/faq.html#best-practices

import argparse
import signal
import sys

import psycopg2
import util
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Move metadata values in the DSpace SQL database from one metadata field to another."
)
parser.add_argument(
    "-i",
    "--input-file",
    help="Path to text file.",
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
    "-f",
    "--from-field-name",
    type=str,
    help="Name of metadata field to move values from, for example: cg.identifier.url",
    required=True,
)
parser.add_argument(
    "-n",
    "--dry-run",
    help="Only print changes that would be made.",
    action="store_true",
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
    type=str,
    help="Name of metadata field to move values to, for example: cg.identifier.dataurl",
    required=True,
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg2.connect(
        f"dbname={args.database_name} user={args.database_user} password={args.database_pass} host='localhost'"
    )

    if args.debug:
        sys.stderr.write(f"{Fore.GREEN}Connected to database.{Fore.RESET}\n")
except psycopg2.OperationalError:
    sys.stderr.write(f"{Fore.RED}Could not connect to database.{Fore.RESET}\n")

    sys.exit(1)

for line in args.input_file:
    # trim any leading or trailing newlines (note we don't want to strip any
    # whitespace from the string that might be in the metadatavalue itself). We
    # only want to move metadatavalues as they are, not clean them up.
    line = line.strip("\n")

    with conn:
        # cursor will be closed after this block exits
        # see: http://initd.org/psycopg/docs/usage.html#with-statement
        with conn.cursor() as cursor:
            from_field_id = util.field_name_to_field_id(cursor, args.from_field_name)

            to_field_id = util.field_name_to_field_id(cursor, args.to_field_name)

            # Get item UUIDs for metadata values that will be updated
            sql = "SELECT dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
            cursor.execute(sql, (from_field_id, line))

            if cursor.rowcount > 0:
                if args.dry_run:
                    if not args.quiet:
                        print(
                            f"{Fore.GREEN}Would move {cursor.rowcount} occurences of: {line}{Fore.RESET}"
                        )

                    # Since this a dry run we can continue to the next line
                    continue

                # Get the records for items with matching metadata. We will use the
                # object IDs to update their last_modified dates.
                matching_records = cursor.fetchall()

                sql = "UPDATE metadatavalue SET metadata_field_id=%s WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value=%s"
                cursor.execute(
                    sql,
                    (
                        to_field_id,
                        from_field_id,
                        line,
                    ),
                )

                if cursor.rowcount > 0:
                    if not args.quiet:
                        print(
                            f"{Fore.GREEN}Moved {cursor.rowcount} occurences of: {line}{Fore.RESET}"
                        )

                # Update the last_modified date for each item we've changed
                for record in matching_records:
                    util.update_item_last_modified(cursor, record[0])

# close database connection before we exit
conn.close()

# close input file
args.input_file.close()

sys.exit(0)
