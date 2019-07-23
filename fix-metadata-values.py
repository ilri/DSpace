#!/usr/bin/env python3

# fix-metadata-values.py 1.0.1
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
# Expects a CSV with two columns: one with "bad" metadata values and one with
# correct values. Basically just a mass search and replace function for DSpace's
# PostgreSQL database. Make sure to do a full `index-discovery -b` afterwards.
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
from colorama import Fore
import csv
import psycopg2
import signal
import sys


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(description='Find and replace metadata values in the DSpace SQL database.')
parser.add_argument('--csv-file', '-i', help='Path to CSV file', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--database-name', '-db', help='Database name', required=True)
parser.add_argument('--database-user', '-u', help='Database username', required=True)
parser.add_argument('--database-pass', '-p', help='Database password', required=True)
parser.add_argument('--debug', '-d', help='Print debug messages to standard error (stderr).', action='store_true')
parser.add_argument('--dry-run', '-n', help='Only print changes that would be made.', action='store_true')
parser.add_argument('--from-field-name', '-f', help='Name of column with values to be replaced.', required=True)
parser.add_argument('--metadata-field-id', '-m', type=int, help='ID of the field in the metadatafieldregistry table.', required=True)
parser.add_argument('--quiet', '-q', help='Do not print progress messages to the screen.', action='store_true')
parser.add_argument('--to-field-name', '-t', help='Name of column with values to replace.', required=True)
args = parser.parse_args()

# open the CSV
reader = csv.DictReader(args.csv_file)

# check if the from/to fields specified by the user exist in the CSV
if args.from_field_name not in reader.fieldnames:
    sys.stderr.write(Fore.RED + 'Specified field "{0}" does not exist in the CSV.\n'.format(args.from_field_name) + Fore.RESET)
    sys.exit(1)
if args.to_field_name not in reader.fieldnames:
    sys.stderr.write(Fore.RED + 'Specified field "{0}" does not exist in the CSV.\n'.format(args.to_field_name) + Fore.RESET)
    sys.exit(1)

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg2.connect("dbname={} user={} password={} host='localhost'".format(args.database_name, args.database_user, args.database_pass))

    if args.debug:
        sys.stderr.write(Fore.GREEN + 'Connected to database.\n' + Fore.RESET)
except psycopg2.OperationalError:
    sys.stderr.write(Fore.RED + 'Could not connect to database.\n' + Fore.RESET)
    sys.exit(1)

for row in reader:
    if row[args.from_field_name] == row[args.to_field_name] and args.debug:
        # sometimes editors send me corrections with identical search/replace patterns
        sys.stderr.write(Fore.YELLOW + 'Skipping identical search and replace for value: {0}\n'.format(row[args.from_field_name]) + Fore.RESET)
        continue

    with conn:
        # cursor will be closed after this block exits
        # see: http://initd.org/psycopg/docs/usage.html#with-statement
        with conn.cursor() as cursor:
            if args.dry_run:
                # resource_type_id 2 is metadata for items
                sql = 'SELECT text_value FROM metadatavalue WHERE resource_type_id=2 AND metadata_field_id=%s AND text_value=%s'
                cursor.execute(sql, (args.metadata_field_id, row[args.from_field_name]))

                if cursor.rowcount > 0 and not args.quiet:
                    print(Fore.GREEN + 'Would fix {0} occurences of: {1}'.format(cursor.rowcount, row[args.from_field_name]) + Fore.RESET)
            else:
                sql = 'UPDATE metadatavalue SET text_value=%s WHERE resource_type_id=2 AND metadata_field_id=%s AND text_value=%s'
                cursor.execute(sql, (row[args.to_field_name], args.metadata_field_id, row[args.from_field_name]))

                if cursor.rowcount > 0 and not args.quiet:
                    print(Fore.GREEN + 'Fixed {0} occurences of: {1}'.format(cursor.rowcount, row[args.from_field_name]) + Fore.RESET)

# close database connection before we exit
conn.close()

# close input file
args.csv_file.close()

sys.exit(0)
