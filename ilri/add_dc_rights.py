#!/usr/bin/env python3
#
# add-dc-rights.py 1.1.2
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
# Add usage rights (dc.rights) to items from CSV.
#
# This script searches for items by handle and adds a dc.rights field to each
# (assuming one does not exist). The format of the CSV file should be:
#
# dc.rights,handle
# CC-BY-NC-ND,10568/72643
# CC-BY-NC-ND,10568/72644
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (for example, in a virtual environment):
#
#   $ pip install colorama psycopg2-binary
#

import argparse
import csv
import signal
import sys

import psycopg2
from colorama import Fore


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser(description="Add usage rights to items from CSV.")
    parser.add_argument(
        "-i",
        "--csv-file",
        help="CSV file containing item handles and rights.",
        required=True,
        type=argparse.FileType("r", encoding="UTF-8"),
    )
    parser.add_argument("-db", "--database-name", help="Database name", required=True)
    parser.add_argument(
        "-u", "--database-user", help="Database username", required=True
    )
    parser.add_argument(
        "-p", "--database-pass", help="Database password", required=True
    )
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
        "-hf",
        "--handle-field-name",
        help='Name of column with handles in "10568/4" format (no URL).',
        default="handle",
    )
    parser.add_argument(
        "-rf",
        "--rights-field-name",
        help="Name of column with usage rights.",
        default="dc.rights",
    )
    args = parser.parse_args()

    # set the signal handler for SIGINT (^C) so we can exit cleanly
    signal.signal(signal.SIGINT, signal_handler)

    # connect to database
    try:
        conn_string = "dbname={database_name} user={database_user} password={database_pass} host=localhost".format(
            database_name=args.database_name,
            database_user=args.database_user,
            database_pass=args.database_pass,
        )
        conn = psycopg2.connect(conn_string)

        if args.debug:
            sys.stderr.write(Fore.GREEN + "Connected to the database.\n" + Fore.RESET)
    except psycopg2.OperationalError:
        sys.stderr.write(Fore.RED + "Unable to connect to the database.\n" + Fore.RESET)

        # close output file before we exit
        args.csv_file.close()

        exit(1)

    # open the CSV
    reader = csv.DictReader(args.csv_file)

    # iterate over rows in the CSV
    for row in reader:
        handle = row[args.handle_field_name]
        rights = row[args.rights_field_name]

        if args.debug:
            sys.stderr.write(
                Fore.GREEN
                + "Finding item with handle {handle}\n".format(handle=handle)
                + Fore.RESET
            )

        with conn:
            # cursor will be closed after this block exits
            # see: http://initd.org/psycopg/docs/usage.html#with-statement
            with conn.cursor() as cursor:
                # get resource_id for current handle
                sql = "SELECT resource_id FROM handle WHERE handle=%s"
                # remember that tuples with one item need a comma after them!
                cursor.execute(sql, (handle,))

                # no resource_id with this handle exists
                if cursor.rowcount == 0:
                    if args.debug:
                        sys.stderr.write(
                            Fore.YELLOW
                            + "Did not find item with handle {handle}, skipping.\n".format(
                                handle=handle
                            )
                            + Fore.RESET
                        )

                    continue

                # multiple resource_id with this handle exist (I don't think this will happen, but better to check)
                elif cursor.rowcount > 1:
                    if args.debug:
                        sys.stderr.write(
                            Fore.YELLOW
                            + "Found multiple items with handle {handle}, skipping.\n".format(
                                handle=handle
                            )
                            + Fore.RESET
                        )

                    continue

                result = cursor.fetchone()
                # result will be an array like: [74525]
                resource_id = result[0]

                # in our test environment I've seen resource_id be NULL for some reason
                if resource_id is None:
                    if args.debug:
                        sys.stderr.write(
                            Fore.YELLOW
                            + "Item with handle {handle} does not have a resource_id, skipping.\n".format(
                                handle=handle
                            )
                            + Fore.RESET
                        )

                    continue

                # Check if this item already has dc.rights metadata
                # resource_type_id 2 is for item metadata, metadata_field_id 53 is dc.rights
                sql = "SELECT text_value FROM metadatavalue WHERE resource_type_id=2 AND resource_id=%s AND metadata_field_id=53"
                # remember that tuples with one item need a comma after them!
                cursor.execute(sql, (resource_id,))

                # if rowcount is greater than 0 there must be existing rights for this item
                if cursor.rowcount > 0:
                    if args.debug:
                        sys.stderr.write(
                            Fore.YELLOW
                            + "Found existing rights metadata for item with handle {handle}, skipping.\n".format(
                                handle=handle
                            )
                            + Fore.RESET
                        )
                    continue

                # no existing rights metadata, so add one
                result = cursor.fetchone()

                if args.dry_run:
                    print(
                        Fore.GREEN
                        + 'Would add rights "{rights}" to item with handle {handle}.\n'.format(
                            rights=rights, handle=handle
                        )
                        + Fore.RESET
                    )
                    continue

                if args.debug:
                    sys.stderr.write(
                        Fore.GREEN
                        + 'Adding rights "{rights}" to item with handle {handle}.\n'.format(
                            rights=rights, handle=handle
                        )
                        + Fore.RESET
                    )

                # metadatavalue IDs come from a PostgreSQL sequence that increments when you call it
                cursor.execute("SELECT nextval('metadatavalue_seq')")
                metadata_value_id = cursor.fetchone()[0]

                # resource_type_id 2 is for item metadata, metadata_field_id 53 is dc.rights
                sql = "INSERT INTO metadatavalue (metadata_value_id, resource_id, metadata_field_id, text_value, place, confidence, resource_type_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(
                    sql, (metadata_value_id, resource_id, 53, rights, 1, -1, 2)
                )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Disconnecting from database.\n" + Fore.RESET)

    # close the database connection before leaving
    conn.close()

    # close output file before we exit
    args.csv_file.close()


def signal_handler(signal, frame):
    sys.exit(1)


if __name__ == "__main__":
    main()
