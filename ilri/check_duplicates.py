#!/usr/bin/env python3

# check-duplicates.py 0.4.3
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Expects a CSV with at least four columns containing id, item titles, types,and
# issue dates to be checked against the DSpace PostgreSQL database for potential
# duplicates. The database must have the trgm extention created in order for
# this to work:
#
#   localhost/database= > CREATE EXTENSION pg_trgm;
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install psycopg colorama
#
# See: https://www.psycopg.org/psycopg3/docs

import argparse
import csv
import signal
import sys
from datetime import datetime

import util
from colorama import Fore
from psycopg import sql


def signal_handler(signal, frame):
    sys.exit(1)


# Compare the item's date issued to that of the potential duplicate
def compare_date_strings(item_date, duplicate_date):
    # Split the item date on "-" to see what format we need to
    # use to create the datetime object.
    if len(item_date.split("-")) == 1:
        date1 = datetime.strptime(item_date, "%Y")
    elif len(item_date.split("-")) == 2:
        date1 = datetime.strptime(item_date, "%Y-%m")
    elif len(item_date.split("-")) == 3:
        date1 = datetime.strptime(item_date, "%Y-%m-%d")

    # Do the same for the potential duplicate's date
    if len(duplicate_date.split("-")) == 1:
        date2 = datetime.strptime(duplicate_date, "%Y")
    elif len(duplicate_date.split("-")) == 2:
        date2 = datetime.strptime(duplicate_date, "%Y-%m")
    elif len(duplicate_date.split("-")) == 3:
        date2 = datetime.strptime(duplicate_date, "%Y-%m-%d")

    # Return the difference between the two dates. Doesn't matter which comes
    # first here because we are getting the absolute to avoid negative days!
    return abs((date1 - date2).days)


parser = argparse.ArgumentParser(description="Find duplicate titles.")
parser.add_argument(
    "-i",
    "--input-file",
    help="Path to input CSV file.",
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
    "--days-threshold",
    type=float,
    help="Threshold for difference of days between item and potential duplicates (default 365).",
    default=365,
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Path to output CSV file.",
    required=True,
    type=argparse.FileType("w"),
)
parser.add_argument(
    "-q",
    "--quiet",
    help="Do not print progress messages to the screen.",
    action="store_true",
)
parser.add_argument(
    "-s",
    "--similarity-threshold",
    type=float,
    help="Similarity threshold, between 0.0 and 1.0 (default 0.6).",
    default=0.6,
)
args = parser.parse_args()

# Column names in the CSV
id_column_name = "id"
criteria1_column_name = "dc.title"
criteria2_column_name = "dcterms.type"
criteria3_column_name = "dcterms.issued"

# open the CSV
reader = csv.DictReader(args.input_file)

# check if the title column exists in the CSV
if criteria1_column_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'Specified criteria one column "{criteria1_column_name}" does not exist in the CSV.'
        + Fore.RESET
    )
    sys.exit(1)
# check if the type column exists in the CSV
if criteria2_column_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'Specified criteria two column "{criteria2_column_name}" does not exist in the CSV.'
        + Fore.RESET
    )
    sys.exit(1)
# check if the date issued column exists in the CSV
if criteria3_column_name not in reader.fieldnames:
    sys.stderr.write(
        Fore.RED
        + f'Specified criteria three column "{criteria3_column_name}" does not exist in the CSV.'
        + Fore.RESET
    )
    sys.exit(1)


# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
conn = util.db_connect(
    args.database_name, args.database_user, args.database_pass, "localhost"
)

# set the connection to read only since we are not writing anything
conn.read_only = True

cursor = conn.cursor()

# Field IDs from the metadatafieldregistry table
criteria1_field_id = util.field_name_to_field_id(cursor, criteria1_column_name)
criteria2_field_id = util.field_name_to_field_id(cursor, criteria2_column_name)
criteria3_field_id = util.field_name_to_field_id(cursor, criteria3_column_name)

with conn:
    # Make sure the pg_trgm extension is installed in the current database
    cursor.execute("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
    if cursor.rowcount == 0:
        sys.stderr.write(
            Fore.RED
            + f"Database '{args.database_name}' is missing the 'pg_trgm' extension.\n"
            + Fore.RESET
        )
        sys.exit(1)

    # Set the similarity threshold for this session. PostgreSQL default is 0.3,
    # which leads to lots of false positives for this use case. Note that the
    # weird syntax here is because of SET not working in in psycopg3.
    #
    # See: https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html#server-side-binding
    cursor.execute(
        sql.SQL(
            "SET pg_trgm.similarity_threshold = {}".format(args.similarity_threshold)
        )
    )

    # Fields for the output CSV
    fieldnames = [
        "id",
        "Your Title",
        "Their Title",
        "Similarity",
        "Your Date",
        "Their Date",
        "Handle",
    ]

    # Write the CSV header
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    for input_row in reader:
        # Check for items with similarity to criteria one (title). Note that
        # this is the fastest variation of this query: using the similarity
        # operator (%, written below twice for escaping) instead of the sim-
        # larity function, as indexes are bound to operators, not functions!
        # Also, if I leave off the item query it takes twice as long!
        sql = "SELECT text_value, dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item WHERE in_archive AND NOT withdrawn) AND metadata_field_id=%s AND text_value %% %s"

        cursor.execute(
            sql,
            (
                criteria1_field_id,
                input_row[criteria1_column_name],
            ),
        )

        # If we have any similarity in criteria one (title), then check type
        if cursor.rowcount > 0:
            duplicate_titles = cursor.fetchall()

            # Iterate over duplicate titles to check their types
            for duplicate_title in duplicate_titles:
                dspace_object_id = duplicate_title[1]

                # Check type of this duplicate title, also making sure that
                # the item is in the archive and not withdrawn.
                sql = "SELECT text_value FROM metadatavalue M JOIN item I ON M.dspace_object_id = I.uuid WHERE M.dspace_object_id=%s AND M.metadata_field_id=%s AND M.text_value=%s AND I.in_archive='t' AND I.withdrawn='f'"

                cursor.execute(
                    sql,
                    (
                        dspace_object_id,
                        criteria2_field_id,
                        input_row[criteria2_column_name],
                    ),
                )

                # This means we didn't match on item type, so let's skip to
                # the next item title.
                if cursor.rowcount == 0:
                    continue

                # Get the date of this potential duplicate. (If we are here
                # then we already confirmed above that the item is both in
                # the archive and not withdrawn, so we don't need to check
                # that again).
                sql = "SELECT text_value FROM metadatavalue M JOIN item I ON M.dspace_object_id = I.uuid WHERE M.dspace_object_id=%s AND M.metadata_field_id=%s"

                cursor.execute(
                    sql,
                    (dspace_object_id, criteria3_field_id),
                )

                # This means that we successfully extracted the date for the
                # potential duplicate.
                if cursor.rowcount > 0:
                    duplicate_item_date = cursor.fetchone()[0]
                # If rowcount is not > 0 then the potential duplicate does
                # not have a date and we have bigger problems. Skip!
                else:
                    continue

                # Get the number of days between the issue dates
                days_difference = compare_date_strings(
                    input_row[criteria3_column_name], duplicate_item_date
                )

                # Items with a similar title, same type, and issue dates
                # within a year or so are likely duplicates. Otherwise,
                # it's possible that items with a similar name could be
                # like Annual Reports where most metadata is the same
                # except the date issued.
                if days_difference <= args.days_threshold:
                    # By this point if we have any matches then they are
                    # similar in title and have an exact match for the type
                    # and an issue date within the threshold. Now we are
                    # reasonably sure it's a duplicate, so get the handle.
                    sql = "SELECT handle FROM handle WHERE resource_id=%s"
                    cursor.execute(sql, (dspace_object_id,))
                    try:
                        handle = f"https://hdl.handle.net/{cursor.fetchone()[0]}"
                    except TypeError:
                        # If we get here then there is no handle for this
                        # item's UUID. Could be that the item was deleted?
                        continue

                    sys.stdout.write(
                        f"{Fore.YELLOW}Found potential duplicate:{Fore.RESET}\n"
                    )

                    # https://alexklibisz.com/2022/02/18/optimizing-postgres-trigram-search.html
                    sql = "SELECT round(similarity(%s, %s)::numeric, 3)"
                    cursor.execute(
                        sql, (input_row[criteria1_column_name], duplicate_title[0])
                    )
                    trgm_similarity = cursor.fetchone()[0]

                    sys.stdout.write(
                        f"{Fore.YELLOW}→ Title:{Fore.RESET} {input_row[criteria1_column_name]} ({trgm_similarity})\n"
                    )
                    sys.stdout.write(f"{Fore.YELLOW}→ Handle:{Fore.RESET} {handle}\n\n")

                    output_row = {
                        "id": input_row[id_column_name],
                        "Your Title": input_row[criteria1_column_name],
                        "Their Title": duplicate_title[0],
                        "Similarity": trgm_similarity,
                        "Your Date": input_row[criteria3_column_name],
                        "Their Date": duplicate_item_date,
                        "Handle": handle,
                    }

                    writer.writerow(output_row)

    # close output file before we exit
    args.output_file.close()

# close input file
args.input_file.close()

sys.exit(0)
