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

# Reads the "filename" and "dc.identifier.url" fields from a CSV,
# fetches the PDF, and generates a thumbnail using GraphicsMagick.
#
# The script is written for Python 3+ and requires PETL and Requests:
#
#   $ pip install petl requests
#
# See: https://petl.readthedocs.org/en/latest
# See: https://requests.readthedocs.org/en/master

import os.path
import petl as etl
import re
import requests
import signal
import subprocess
import sys


def signal_handler(signal, frame):
    sys.exit(0)


# Process thumbnails from filename.pdf to filename.jpg using GraphicsMagick
# and Ghostscript. Equivalent to the following shell invocation:
#
#   gm convert -quality 85 -thumbnail x400 -flatten 64661.pdf\[0\] cover.jpg
#
def create_thumbnail(record):

    filename = record[0]
    thumbnail = os.path.splitext(filename)[0] + '.jpg'
    # check if we already have a thumbnail
    if os.path.isfile(thumbnail):
        print("> Thumbnail for", filename, "already exists")
    else:
        print("> Creating thumbnail for", filename)
        subprocess.run(["gm", "convert", "-quality", "85", "-thumbnail", "x400", "-flatten", filename + "[0]", thumbnail])

    return


def download_bitstream(record):

    # some records have multiple URLs separated by "||"
    pattern = re.compile("\|\|")
    urls = pattern.split(record[0])
    filenames = pattern.split(record[1])
    for url, filename in zip(urls, filenames):
        print("URL: " + url)
        print("File: " + filename)

        # check if file exists
        if os.path.isfile(filename):
            print(">", filename, "already downloaded")
        else:
            print("> Downloading", filename)

            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as fd:
                    for chunk in response:
                        fd.write(chunk)
            else:
                print("> Download failed, I'll try again next time")

    return


# make sure the user passed us the name of a CSV on the command line
if len(sys.argv) == 2:
    # read records from the CSV
    records = etl.fromcsv(sys.argv[1])
else:
    print("Usage: " + sys.argv[0] + " filename.csv")
    exit()

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# get URL and filename fields for each record
# make sure other URL fields like dc.identifier.url[] etc are merged into this one and filename column exists!
for record in etl.values(records, 'dc.identifier.url', 'filename'):
    download_bitstream(record)

    # maybe only generate thumbnails if -t is passed?
    #create_thumbnail(record)
