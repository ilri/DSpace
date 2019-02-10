#!/usr/bin/env python
#
# add-orcid-identifiers-csv.py 1.0.0
#
# Copyright 2018 Alan Orth.
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
# Add ORCID identifiers to items for a given author name from CSV.
#
# We had previously migrated the ORCID identifiers from CGSpace's authority Solr
# core to cg.creator.id fields in matching items, but now we want to add them to
# other matching items in a more arbitrary fashion. Items that are older or were
# uploaded in batch did not have matching authors in the authority core, so they
# did not benefit from that migration, for example.
#
# This script searches for items by author name and adds a cg.creator.id field
# to each (assuming one does not exist). The format of the CSV file should be:
#
# dc.contributor.author,cg.creator.id
# "Orth, Alan",Alan S. Orth: 0000-0002-1735-7458
# "Orth, A.",Alan S. Orth: 0000-0002-1735-7458
#
# The order of authors in dc.contributor.author is respected and mirrored in the
# new cg.creator.id fields.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama psycopg2-binary
#

import argparse
from colorama import Fore
import csv
import psycopg2
import re
import signal
import sys


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser(description='Add ORCID identifiers to items for a given author name from CSV. Respects the author order from the dc.contributor.author field.')
    parser.add_argument('--author-field-name', '-f', help='Name of column with author names.', default='dc.contributor.author')
    parser.add_argument('--csv-file', '-i', help='CSV file containing author names and ORCID identifiers.', required=True, type=argparse.FileType('r', encoding='UTF-8'))
    parser.add_argument("--database-name", "-db", help='Database name', required=True)
    parser.add_argument("--database-user", "-u", help='Database username', required=True)
    parser.add_argument("--database-pass", "-p", help='Database password', required=True)
    parser.add_argument('--debug', '-d', help='Print debug messages to standard error (stderr).', action='store_true')
    parser.add_argument('--dry-run', '-n', help='Only print changes that would be made.', action='store_true')
    parser.add_argument('--orcid-field-name', '-o', help='Name of column with creators in "Name: 0000-0000-0000-0000" format.', default='cg.creator.id')
    args = parser.parse_args()

    # set the signal handler for SIGINT (^C) so we can exit cleanly
    signal.signal(signal.SIGINT, signal_handler)

    # connect to database
    try:
        conn_string = 'dbname={0} user={1} password={2} host=localhost'.format(args.database_name, args.database_user, args.database_pass)
        conn = psycopg2.connect(conn_string)

        if args.debug:
            sys.stderr.write(Fore.GREEN + 'Connected to the database.\n' + Fore.RESET)
    except psycopg2.OperationalError:
        sys.stderr.write(Fore.RED + 'Unable to connect to the database.\n' + Fore.RESET)

        # close output file before we exit
        args.csv_file.close()

        exit(1)

    # open the CSV
    reader = csv.DictReader(args.csv_file)

    # iterate over rows in the CSV
    for row in reader:
        author_name = row[args.author_field_name]

        if args.debug:
            sys.stderr.write(Fore.GREEN + 'Finding items with author name: {0}\n'.format(author_name) + Fore.RESET)

        with conn:
            # cursor will be closed after this block exits
            # see: http://initd.org/psycopg/docs/usage.html#with-statement
            with conn.cursor() as cursor:
                # find all item metadata records with this author name
                # resource_type_id 2 is item metadata, metadata_field_id 3 is author
                sql = 'SELECT resource_id, place FROM metadatavalue WHERE resource_type_id=2 AND metadata_field_id=3 AND text_value=%s'
                # remember that tuples with one item need a comma after them!
                cursor.execute(sql, (author_name,))
                records_with_author_name = cursor.fetchall()

                if len(records_with_author_name) >= 0:
                    if args.debug:
                        sys.stderr.write(Fore.GREEN + 'Found {0} items.\n'.format(len(records_with_author_name)) + Fore.RESET)

                    # extract cg.creator.id text to add from CSV and strip leading/trailing whitespace
                    text_value = row[args.orcid_field_name].strip()
                    # extract the ORCID identifier from the cg.creator.id text field in the CSV
                    orcid_identifier_pattern = re.compile('[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}')
                    orcid_identifier_match = orcid_identifier_pattern.search(text_value)

                    # sanity check to make sure we extracted the ORCID identifier from the cg.creator.id text in the CSV
                    if orcid_identifier_match is None:
                        if args.debug:
                            sys.stderr.write(Fore.YELLOW + 'Skipping invalid ORCID identifier in "{0}".\n'.format(text_value) + Fore.RESET)
                        continue

                    # we only expect one ORCID identifier, so if it matches it will be group "0"
                    # see: https://docs.python.org/3/library/re.html
                    orcid_identifier = orcid_identifier_match.group(0)

                    # iterate over results for current author name to add cg.creator.id metadata
                    for record in records_with_author_name:
                        resource_id = record[0]
                        # "place" is the order of a metadata value so we can add the cg.creator.id metadata matching the author order
                        place = record[1]
                        confidence = -1

                        # get the metadata_field_id for the cg.creator.id field
                        sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=2 AND element='creator' AND qualifier='id'"
                        cursor.execute(sql)
                        metadata_field_id = cursor.fetchall()[0]

                        # check if there is an existing cg.creator.id with this author's ORCID identifier for this item (without restricting the "place")
                        # note that the SQL here is quoted differently to allow us to use LIKE with % wildcards with our paremeter subsitution
                        # resource_type_id 2 is item metadata
                        sql = "SELECT * from metadatavalue WHERE resource_id=%s AND metadata_field_id=%s AND text_value LIKE '%%' || %s || '%%' AND confidence=%s AND resource_type_id=2"

                        cursor.execute(sql, (resource_id, metadata_field_id, orcid_identifier, confidence))
                        records_with_orcid_identifier = cursor.fetchall()

                        if len(records_with_orcid_identifier) == 0:
                            if args.dry_run:
                                print('Would add ORCID identifier "{0}" to item {1}.'.format(text_value, resource_id))
                                continue

                            print('Adding ORCID identifier "{0}" to item {1}.'.format(text_value, resource_id))

                            # metadatavalue IDs come from a PostgreSQL sequence that increments when you call it
                            cursor.execute("SELECT nextval('metadatavalue_seq')")
                            metadata_value_id = cursor.fetchone()[0]

                            sql = 'INSERT INTO metadatavalue (metadata_value_id, resource_id, metadata_field_id, text_value, place, confidence, resource_type_id) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                            cursor.execute(sql, (metadata_value_id, resource_id, metadata_field_id, text_value, place, confidence, 2))
                        else:
                            if args.debug:
                                sys.stderr.write(Fore.GREEN + 'Item {0} already has an ORCID identifier for {1}.\n'.format(resource_id, text_value) + Fore.RESET)

    if args.debug:
        sys.stderr.write(Fore.GREEN + 'Disconnecting from database.\n' + Fore.RESET)

    # close the database connection before leaving
    conn.close()

    # close output file before we exit
    args.csv_file.close()


def signal_handler(signal, frame):
    sys.exit(1)


if __name__ == "__main__":
    main()
