#!/usr/bin/env python3
#
# update-orcids.py v0.1.4
#
# Copyright Alan Orth.
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
#   $ pip install colorama
#

import argparse
import logging
import re
import signal
import sys

import util
from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Update ORCID records in the DSpace PostgreSQL database."
)
parser.add_argument(
    "-i",
    "--input-file",
    help='Path to input file containing ORCIDs in format "Alan S. Orth: 0000-0002-1735-7458".',
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
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
args = parser.parse_args()

# The default log level is WARNING, but we want to set it to DEBUG or INFO
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Set the global log format
logging.basicConfig(format="[%(levelname)s] %(message)s")

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
conn = util.db_connect(
    args.database_name, args.database_user, args.database_pass, "localhost"
)

cursor = conn.cursor()

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
                + f'Skipping invalid ORCID identifier in "{line}".\n'
                + Fore.RESET
            )
        continue

    # we only expect one ORCID identifier, so if it matches it will be group "0"
    # see: https://docs.python.org/3/library/re.html
    orcid_identifier = orcid_identifier_match.group(0)

    metadata_field_id = util.field_name_to_field_id(cursor, "cg.creator.identifier")

    # note that the SQL here is quoted differently to allow us to use
    # LIKE with % wildcards with our paremeter subsitution
    sql = "SELECT text_value, dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND text_value!=%s"
    cursor.execute(sql, (metadata_field_id, orcid_identifier, line))

    # Get the records for items with matching metadata. We will use the
    # object IDs to update their last_modified dates.
    matching_records = cursor.fetchall()

    if args.dry_run:
        if cursor.rowcount > 0 and not args.quiet:
            logger.info(
                Fore.GREEN
                + f"(DRY RUN) Fixed {cursor.rowcount} occurences of: {line}"
                + Fore.RESET
            )
    else:
        sql = "UPDATE metadatavalue SET text_value=%s WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND text_value!=%s"
        cursor.execute(
            sql,
            (
                line,
                metadata_field_id,
                orcid_identifier,
                line,
            ),
        )

        if cursor.rowcount > 0 and not args.quiet:
            logger.info(
                Fore.GREEN
                + f"Fixed {cursor.rowcount} occurences of: {line}"
                + Fore.RESET
            )

        # Update the last_modified date for each item we've changed
        for record in matching_records:
            util.update_item_last_modified(cursor, record[1])


# commit changes when we're done
if not args.dry_run:
    conn.commit()

# close database connection before we exit
conn.close()

# close input file
args.input_file.close()

sys.exit(0)
