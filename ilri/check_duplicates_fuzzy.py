#!/usr/bin/env python3

# check-duplicates.py 0.4.0
#
# Copyright Alan Orth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
#   $ pip install psycopg2-binary colorama
#
# See: http://initd.org/psycopg
# See: http://initd.org/psycopg/docs/usage.html#with-statement
# See: http://initd.org/psycopg/docs/faq.html#best-practices

import argparse
import csv
import signal
import sys
from datetime import datetime

import psycopg2
from colorama import Fore

# Column names in the CSV
id_column_name = "id"
criteria1_column_name = "dc.title"
criteria2_column_name = "dcterms.type"
criteria3_column_name = "dcterms.issued"
# Field IDs from the metadatafieldregistry table
criteria1_field_id = 64
criteria2_field_id = 191
criteria3_field_id = 170


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
try:
    conn = psycopg2.connect(
        f"dbname={args.database_name} user={args.database_user} password={args.database_pass} host=localhost"
    )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Connected to database.\n" + Fore.RESET)
except psycopg2.OperationalError:
    sys.stderr.write(Fore.RED + "Could not connect to database.\n" + Fore.RESET)
    sys.exit(1)

with conn:
    # cursor will be closed after this block exits
    # see: http://initd.org/psycopg/docs/usage.html#with-statement
    with conn.cursor() as cursor:
        # Make sure the pg_trgm extension is installed in the current database
        cursor.execute("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
        if cursor.rowcount == 0:
            sys.stderr.write(
                Fore.RED
                + f"Database '{args.database_name}' is missing the 'pg_trgm' extension.\n"
                + Fore.RESET
            )
            sys.exit(1)

        # Set the similarity threshold for this session. PostgreSQL default is
        # 0.3, which leads to lots of false positives for this use case.
        cursor.execute(
            "SET pg_trgm.similarity_threshold = %s", (args.similarity_threshold,)
        )

        # Fields for the output CSV
        fieldnames = [
            "id",
            "Your Title",
            "Their Title",
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
            sql = "SELECT text_value, dspace_object_id FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item) AND metadata_field_id=%s AND LEVENSHTEIN_LESS_EQUAL(LOWER(%s), LEFT(LOWER(text_value), 255), 3) <= 3"

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
                        handle = f"https://hdl.handle.net/{cursor.fetchone()[0]}"

                        sys.stdout.write(
                            f"{Fore.YELLOW}Found potential duplicate:{Fore.RESET}\n"
                        )
                        sys.stdout.write(
                            f"{Fore.YELLOW}→ Title:{Fore.RESET} {input_row[criteria1_column_name]}\n"
                        )
                        sys.stdout.write(
                            f"{Fore.YELLOW}→ Handle:{Fore.RESET} {handle}\n\n"
                        )

                        output_row = {
                            "id": input_row[id_column_name],
                            "Your Title": input_row[criteria1_column_name],
                            "Their Title": duplicate_title[0],
                            "Your Date": input_row[criteria3_column_name],
                            "Their Date": duplicate_item_date,
                            "Handle": handle,
                        }

                        writer.writerow(output_row)

        # close output file before we exit
        args.output_file.close()


# close database connection before we exit
conn.close()

# close input file
args.input_file.close()

sys.exit(0)
