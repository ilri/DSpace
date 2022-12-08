#!/usr/bin/env python3

# move-metadata-values.py 0.0.1
#
# Copyright 2021 Alan Orth.
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
from colorama import Fore
import psycopg2
import signal
import sys


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Move metadata values in the DSpace SQL database from one metadata field ID to another."
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
    "-n",
    "--dry-run",
    help="Only print changes that would be made.",
    action="store_true",
)
parser.add_argument(
    "-f",
    "--from-field-id",
    help="Old metadata field ID.",
    required=True,
)
parser.add_argument(
    "-t",
    "--to-field-id",
    type=int,
    help="New metadata field ID.",
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

for line in args.input_file:
    # trim any leading or trailing newlines (note we don't want to strip any
    # whitespace from the string that might be in the metadatavalue itself). We
    # only want to move metadatavalues as they are, not clean them up.
    line = line.strip("\n")

    with conn:
        # cursor will be closed after this block exits
        # see: http://initd.org/psycopg/docs/usage.html#with-statement
        with conn.cursor() as cursor:
            if args.dry_run:
                sql = "SELECT text_value FROM metadatavalue WHERE dspace_object_id IN (SELECT uuid FROM item) AND metadata_field_id=%s AND text_value=%s"
                cursor.execute(sql, (args.from_field_id, line))

                if cursor.rowcount > 0 and not args.quiet:
                    print(
                        Fore.GREEN
                        + "Would move {0} occurences of: {1}".format(
                            cursor.rowcount, line
                        )
                        + Fore.RESET
                    )
            else:
                sql = "UPDATE metadatavalue SET metadata_field_id=%s WHERE dspace_object_id IN (SELECT uuid FROM item) AND metadata_field_id=%s AND text_value=%s"
                cursor.execute(
                    sql,
                    (
                        args.to_field_id,
                        args.from_field_id,
                        line,
                    ),
                )

                if cursor.rowcount > 0 and not args.quiet:
                    print(
                        Fore.GREEN
                        + "Moved {0} occurences of: {1}".format(cursor.rowcount, line)
                        + Fore.RESET
                    )

# close database connection before we exit
conn.close()

# close input file
args.input_file.close()

sys.exit(0)
