#!/usr/bin/env python3
#
# update-orcids.py v0.1.1
#
# Copyright 2022 Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Expects a text file with author names and ORCID identifiers in the following
# format:
#
# 	Jose Polania: 0000-0002-1186-0503
# 	Joseph Fargione: 0000-0002-0636-5380
# 	Joseph M. Sandro: 0000-0002-8311-2299
#
# Will check existing ORCID metadata to make sure they use the author's latest
# name format.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install psycopg colorama
#

import argparse
import re
import signal
import sys

import psycopg
import util
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Update ORCID records in the DSpace PostgreSQL database."
)
parser.add_argument(
    "-i",
    "--input-file",
    help=f'Path to input file containing ORCIDs in format "Alan S. Orth: 0000-0002-1735-7458".',
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
    "-m",
    "--metadata-field-id",
    type=int,
    help="ID of the ORCID field in the metadatafieldregistry table.",
    required=True,
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg.connect(
        "dbname={} user={} password={} host='localhost'".format(
            args.database_name, args.database_user, args.database_pass
        )
    )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Connected to database.\n" + Fore.RESET)
except psycopg.OperationalError:
    sys.stderr.write(Fore.RED + "Could not connect to database.\n" + Fore.RESET)
    sys.exit(1)

# Use read().splitlines() so we don't get newlines after each line, though I'm
# not sure if we should also be stripping?
for line in args.input_file.read().splitlines():
    # extract the ORCID identifier from the current line
    orcid_identifier_pattern = re.compile(
        r"[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}"
    )
    orcid_identifier_match = orcid_identifier_pattern.search(line)

    # sanity check to make sure we extracted the ORCID identifier
    if orcid_identifier_match is None:
        if args.debug:
            sys.stderr.write(
                Fore.YELLOW
                + 'Skipping invalid ORCID identifier in "{0}".\n'.format(line)
                + Fore.RESET
            )
        continue

    # we only expect one ORCID identifier, so if it matches it will be group "0"
    # see: https://docs.python.org/3/library/re.html
    orcid_identifier = orcid_identifier_match.group(0)

    # see: https://www.psycopg.org/psycopg3/docs/basic/transactions.html#transaction-context
    with conn.cursor() as cursor:
        # note that the SQL here is quoted differently to allow us to use
        # LIKE with % wildcards with our paremeter subsitution
        sql = "SELECT text_value, dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND text_value!=%s"
        cursor.execute(sql, (args.metadata_field_id, orcid_identifier, line))

        # Get the records for items with matching metadata. We will use the
        # object IDs to update their last_modified dates.
        matching_records = cursor.fetchall()

        if args.dry_run:
            if cursor.rowcount > 0 and not args.quiet:
                print(
                    Fore.GREEN
                    + "Would fix {0} occurences of: {1}".format(cursor.rowcount, line)
                    + Fore.RESET
                )
        else:
            sql = "UPDATE metadatavalue SET text_value=%s WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND text_value!=%s"
            cursor.execute(
                sql,
                (
                    line,
                    args.metadata_field_id,
                    orcid_identifier,
                    line,
                ),
            )

            if cursor.rowcount > 0 and not args.quiet:
                print(
                    Fore.GREEN
                    + "Fixed {0} occurences of: {1}".format(cursor.rowcount, line)
                    + Fore.RESET
                )

            # Update the last_modified date for each item we've changed
            for record in matching_records:
                util.update_item_last_modified(cursor, record[1])


# close database connection before we exit
conn.close()

# close input file
args.input_file.close()

sys.exit(0)
