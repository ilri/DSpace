#!/usr/bin/env python
#
# generate-thumbnails.py 1.0.0
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

# Reads the filename and URL fields from a CSV, fetches the PDF, and generates
# a thumbnail using GraphicsMagick (must be installed on the host).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama requests
#
# See: https://requests.readthedocs.org/en/master

import argparse
from colorama import Fore
import csv
import os.path
import re
import requests
import signal
import subprocess
import sys


def signal_handler(signal, frame):
    sys.exit(1)


parser = argparse.ArgumentParser(description='Download PDFs and generate thumbnails from files in a CSV.')
parser.add_argument('--csv-file', '-i', help='Path to CSV file', required=True, type=argparse.FileType('r', encoding='UTF-8'))
parser.add_argument('--debug', '-d', help='Print debug messages to standard error (stderr).', action='store_true')
parser.add_argument('--dry-run', '-n', help='Only print changes that would be made.', action='store_true')
parser.add_argument('--filename-field-name', '-f', help='Name of column with thumbnail filenames.', default='filename')
parser.add_argument('--quiet', '-q', help='Do not print progress messages to the screen.', action='store_true')
parser.add_argument('--url-field-name', '-u', help='Name of column with URLs for the PDFs.', default='dc.description.url')
parser.add_argument('--download-only', '-w', help='Only download the PDFs.')
args = parser.parse_args()

# open the CSV
reader = csv.DictReader(args.csv_file)

# check if the filename and URL fields specified by the user exist in the CSV
if args.filename_field_name not in reader.fieldnames:
    sys.stderr.write(Fore.RED + 'Specified field "{}" does not exist in the CSV.\n'.format(args.filename_field_name) + Fore.RESET)
    sys.exit(1)
if args.url_field_name not in reader.fieldnames:
    sys.stderr.write(Fore.RED + 'Specified field "{0}" does not exist in the CSV.\n'.format(args.url_field_name) + Fore.RESET)
    sys.exit(1)

# Process thumbnails from filename.pdf to filename.jpg using GraphicsMagick
# and Ghostscript. Equivalent to the following shell invocation:
#
#   gm convert -quality 85 -thumbnail x400 -flatten 64661.pdf\[0\] cover.jpg
#
def create_thumbnail(row):

    filename = row[args.filename_field_name]
    thumbnail = os.path.splitext(filename)[0] + '.jpg'
    # check if we already have a thumbnail
    if os.path.isfile(thumbnail) and args.debug:
        print(Fore.YELLOW + '> Thumbnail for {} already exists.\n'.format(filename) + Fore.RESET)
    else:
        print(Fore.Green + '> Creating thumbnail for {}...'.format(filename) + Fore.RESET)
        subprocess.run(["gm", "convert", "-quality", "85", "-thumbnail", "x400", "-flatten", filename + "[0]", thumbnail])

    return


def download_bitstream(row):

    # some records have multiple URLs separated by "||"
    pattern = re.compile("\|\|")
    urls = pattern.split(row[args.url_field_name])
    filenames = pattern.split(row[args.filename_field_name])
    for url, filename in zip(urls, filenames):
        if args.debug:
            print('URL: {}'.format(url))
            print('File: {}'.format(filename))

        # check if file exists
        if os.path.isfile(filename):
            if args.debug:
                print(Fore.YELLOW + '> {} already downloaded.'.format(filename) + Fore.RESET)
        else:
            if args.debug:
                print(Fore.GREEN + '> Downloading {}...'.format(filename) + Fore.RESET)

            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as fd:
                    for chunk in response:
                        fd.write(chunk)
            else:
                print(Fore.RED + '> Download failed, I will try again next time.' + Fore.RESET)

    return


# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

for row in reader:
    download_bitstream(row)

    # maybe only generate thumbnails if -t is passed?
    #create_thumbnail(row)
