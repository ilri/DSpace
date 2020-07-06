#!/usr/bin/env python3
#
# resolve-addresses.py 0.3.1
#
# Copyright 2019 Alan Orth.
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
# Queries the IPAPI.co API for information about IP addresses read from a text
# file. The text file should have one address per line (comments and invalid
# lines are skipped).
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install requests requests-cache colorama
#

import argparse
from colorama import Fore
import csv
from datetime import timedelta
import ipaddress
import requests
import requests_cache
import signal
import sys


def valid_ip(address):
    try:
        ipaddress.ip_address(address)

        return True

    except ValueError:
        return False


# read IPs from a text file, one per line
def read_addresses_from_file():

    # initialize an empty list for IP addresses
    addresses = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # skip any lines that aren't valid IPs
        if not valid_ip(line):
            continue

        # iterate over results and add addresses that aren't already present
        if line not in addresses:
            addresses.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_addresses(addresses)


def resolve_addresses(addresses):

    fieldnames = ['ip', 'org', 'asn', 'country']
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # enable transparent request cache with 30 day expiry
    expire_after = timedelta(days=30)
    # cache HTTP 200 responses
    requests_cache.install_cache('ipapi-response-cache', expire_after=expire_after)

    # prune old cache entries
    requests_cache.core.remove_expired_responses()

    # iterate through our addresses
    for address in addresses:
        if args.debug:
            sys.stderr.write(Fore.GREEN + f'Looking up the address: {address}\n' + Fore.RESET)

        # build request URL for current address
        request_url = f'https://ipapi.co/{address}/json'

        request = requests.get(request_url)

        if args.debug and request.from_cache:
            sys.stderr.write(Fore.GREEN + 'Request in cache.\n' + Fore.RESET)

        # if request status 200 OK
        if request.status_code == requests.codes.ok:
            data = request.json()

            address_org = data['org']
            address_asn = data['asn']
            address_country = data['country']

            writer.writerow({'ip': address, 'org': address_org, 'asn': address_asn, 'country': address_country})

        # if request status not 200 OK
        else:
            sys.stderr.write(Fore.RED + 'Error: request failed.\n' + Fore.RESET)
            exit(1)

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(description='Query the public IPAPI.co API for information associated with a list of IP addresses from a text file.')
parser.add_argument('-d', '--debug', help='Print debug messages to standard error (stderr).', action='store_true')
parser.add_argument('-i', '--input-file', help='File name containing IP addresses to resolve.', required=True, type=argparse.FileType('r'))
parser.add_argument('-o', '--output-file', help='File name to save CSV output.', required=True, type=argparse.FileType('w'))
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the addresses from there
if args.input_file:
    read_addresses_from_file()

exit()
