#!/usr/bin/env python
#
# delete-metadata-values.py 1.0.0
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
# Expects a CSV with one column of metadata values to delete, for example:
#
# delete
# "some value to delete"
#
#   $ ./delete-metadata-values.py -db database -u user -p password -m 3 -f delete -i file.csv
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install psycopg2-binary
#

import argparse
import csv
import psycopg2
import signal
import sys


def signal_handler(signal, frame):
    sys.exit(0)


parser = argparse.ArgumentParser(description='Delete metadata values in the DSpace SQL database.')
parser.add_argument('--csv-file', '-i', help='Path to CSV file', type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--database-name', '-db', help='Database name', required=True)
parser.add_argument('--database-user', '-u', help='Database username', required=True)
parser.add_argument('--database-pass', '-p', help='Database password', required=True)
parser.add_argument('--debug', '-d', help='Print debug messages to standard error (stderr).', action='store_true')
parser.add_argument('--dry-run', '-n', help='Only print changes that would be made.', action='store_true')
parser.add_argument('--from-field-name', '-f', help='Name of column with values to be deleted', required=True)
parser.add_argument('--metadata-field-id', '-m', type=int, help='ID of the field in the metadatafieldregistry table', required=True)
parser.add_argument('--quiet', '-q', help='Do not print progress messages to the screen.', action='store_true')
args = parser.parse_args()

# open the CSV
reader = csv.DictReader(args.csv_file)

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# connect to database
try:
    conn = psycopg2.connect("dbname={} user={} password={} host='localhost'".format(args.database_name, args.database_user, args.database_pass))

    if args.debug:
        sys.stderr.write('Connected to database.\n')
except psycopg2.OperationalError:
    sys.stderr.write('Could not connect to database.\n')
    sys.exit(1)

for row in reader:
    with conn:
        # cursor will be closed after this block exits
        # see: http://initd.org/psycopg/docs/usage.html#with-statement
        with conn.cursor() as cursor:
            if args.dry_run:
                # resource_type_id 2 is metadata for items
                sql = 'SELECT text_value FROM metadatavalue WHERE resource_type_id=2 AND metadata_field_id=%s AND text_value=%s'
                cursor.execute(sql, (args.metadata_field_id, row[args.from_field_name]))

                if cursor.rowcount > 0 and not args.quiet:
                    print('Would delete {0} occurences of: {1}'.format(cursor.rowcount, row[args.from_field_name]))

            else:
                sql = 'DELETE from metadatavalue WHERE resource_type_id=2 AND metadata_field_id=%s AND text_value=%s'
                cursor.execute(sql, (args.metadata_field_id, row[args.from_field_name]))

                if cursor.rowcount > 0 and not args.quiet:
                    print('Deleted {0} occurences of: {1}'.format(cursor.rowcount, row[args.from_field_name]))

# close database connection before we exit
conn.close()

# close the input file
args.csv_file.close()

sys.exit(0)
