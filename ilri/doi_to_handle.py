#!/usr/bin/env python3
#
# doi-to-handle.py 0.0.2
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
# This script is written for Python 3.6+.
#

import argparse
import csv
import signal
import sys

import util


def resolve_doi(dois):
    # metadata_field_id for metadata values (from metadatafieldregistry and
    # might differ from site to site).
    title_metadata_field_id = 64
    handle_metadata_field_id = 25
    doi_metadata_field_id = 220

    print(f"Looking up {doi} in database")

    cursor = conn.cursor()

    with conn.transaction():
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

            return
        else:
            print(f"Not found: {doi}")

            return

        # get the title
        sql = "SELECT text_value FROM metadatavalue WHERE metadata_field_id=%s AND dspace_object_id=%s"
        cursor.execute(sql, (title_metadata_field_id, dspace_object_id))

        if cursor.rowcount != 1:
            print(f"Missing title for {doi}, skipping")

            return

        title = cursor.fetchone()[0]

        # get the handle
        cursor.execute(sql, (handle_metadata_field_id, dspace_object_id))

        if cursor.rowcount != 1:
            print(f"Missing handle for {doi}, skipping")

            return

        handle = cursor.fetchone()[0]

        row = {
            "title": title,
            "handle": handle,
            "doi": doi,
        }

        writer.writerow(row)


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    # close database connection before we exit
    conn.close()

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
conn = util.db_connect(
    args.database_name, args.database_user, args.database_pass, "localhost"
)

# Set this connection to be read only since we are not modifying the database
conn.read_only = True

# field names for the CSV
fieldnames = ["title", "handle", "doi"]

writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
writer.writeheader()

dois = util.read_dois_from_file(args.input_file)
for doi in dois:
    resolve_doi(doi)

# close output file before we exit
args.output_file.close()

# close database connection before we exit
conn.close()

exit()
