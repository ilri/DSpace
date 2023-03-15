#!/usr/bin/env python3
#
# doi-to-handle.py 0.0.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# This script was written to produce a list of Handles from a list of DOIs. It
# reads a text file with DOIs (one per line) and looks in the local DSpace SQL
# database to find the Handle for any item with that DOI. We used it to target
# the Tweeting of certain items in order to get Altmetric to make the link be-
# tween the Handle and the DOI.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend setting up a Python virtual environment):
#
#   $ pip install colorama psycopg2
#

import argparse
from colorama import Fore
import csv
import psycopg2
import signal
import sys

# read dois from a text file, one per line
def read_dois_from_file():

    # initialize an empty list for DOIs
    dois = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add dois that aren't already present
        if line not in dois:
            dois.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_dois(dois)


def resolve_dois(dois):

    # metadata_field_id for metadata values (from metadatafieldregistry and
    # might differ from site to site).
    title_metadata_field_id = 64
    handle_metadata_field_id = 25
    doi_metadata_field_id = 220

    # field names for the CSV
    fieldnames = ["title", "handle", "doi"]

    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # iterate through our DOIs
    for doi in dois:
        print(f"Looking up {doi} in database")

        with conn:
            # cursor will be closed after this block exits
            # see: http://initd.org/psycopg/docs/usage.html#with-statement
            with conn.cursor() as cursor:
                # make a temporary string we can use with the PostgreSQL regex
                doi_string = f".*{doi}.*"

                # get the dspace_object_id for the item with this DOI
                sql = "SELECT dspace_object_id FROM metadatavalue WHERE metadata_field_id=%s AND text_value ~* %s"
                cursor.execute(
                    sql,
                    (doi_metadata_field_id, doi_string),
                )

                # make sure rowcount is exactly 1, because some DOIs are used
                # multiple times and I ain't got time for that right now
                if cursor.rowcount == 1 and not args.quiet:
                    dspace_object_id = cursor.fetchone()[0]
                    print(f"Found {doi}, DSpace object: {dspace_object_id}")
                elif cursor.rowcount > 1 and not args.quiet:
                    print(f"Found multiple items for {doi}")

                    continue
                else:
                    print(f"Not found: {doi}")

                    continue

                # get the title
                sql = "SELECT text_value FROM metadatavalue WHERE metadata_field_id=%s AND dspace_object_id=%s"
                cursor.execute(sql, (title_metadata_field_id, dspace_object_id))

                if cursor.rowcount != 1:
                    print(f"Missing title for {doi}, skipping")

                    continue

                title = cursor.fetchone()[0]

                # get the handle
                cursor.execute(sql, (handle_metadata_field_id, dspace_object_id))

                if cursor.rowcount != 1:
                    print(f"Missing handle for {doi}, skipping")

                    continue

                handle = cursor.fetchone()[0]

                row = {
                    "title": title,
                    "handle": handle,
                    "doi": doi,
                }

            writer.writerow(row)

    # close database connection before we exit
    conn.close()

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query DSpace database for item metadata based on a list of DOIs in a text file."
)
parser.add_argument(
    "-d",
    "--debug",
    help="Print debug messages to standard error (stderr).",
    action="store_true",
)
parser.add_argument("-db", "--database-name", help="Database name", required=True)
parser.add_argument(
    "-i",
    "--input-file",
    help="File name containing DOIs to resolve.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-o",
    "--output-file",
    help="File name to save CSV output.",
    required=True,
    type=argparse.FileType("w"),
)
parser.add_argument("-p", "--database-pass", help="Database password", required=True)
parser.add_argument(
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
parser.add_argument("-u", "--database-user", help="Database username", required=True)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg2.connect(
        "dbname={} user={} password={} host='localhost'".format(
            args.database_name, args.database_user, args.database_pass
        )
    )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Connected to database.\n" + Fore.RESET)
except psycopg2.OperationalError:
    sys.stderr.write(Fore.RED + "Could not connect to database.\n" + Fore.RESET)
    sys.exit(1)


read_dois_from_file()

exit()
