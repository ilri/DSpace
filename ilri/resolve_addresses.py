#!/usr/bin/env python3
#
# resolve-addresses.py 0.4.1
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the IPAPI.co API for information about IP addresses read from a text
# file. The text file should have one address per line (comments and invalid
# lines are skipped). Optionally looks up IPs in the AbuseIPDB.com if you pro-
# vide an API key.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install requests requests-cache colorama
#

import argparse
import csv
import ipaddress
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
from colorama import Fore


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
    if args.abuseipdb_api_key:
        fieldnames = ["ip", "org", "asn", "country", "abuseConfidenceScore"]
    else:
        fieldnames = ["ip", "org", "asn", "country"]

    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # enable transparent request cache with thirty-day expiry
    expire_after = timedelta(days=30)
    # cache HTTP 200 responses
    requests_cache.install_cache("requests-cache", expire_after=expire_after)

    # prune old cache entries
    requests_cache.delete()

    # iterate through our addresses
    for address in addresses:
        print(f"Looking up {address} in IPAPI")

        # build IPAPI request URL for current address
        request_url = f"https://ipapi.co/{address}/json"

        request = requests.get(request_url)

        if args.debug and request.from_cache:
            sys.stderr.write(Fore.GREEN + "Request in cache.\n" + Fore.RESET)

        # if request status 200 OK
        if request.status_code == requests.codes.ok:
            data = request.json()

            address_org = data["org"]
            address_asn = data["asn"]
            address_country = data["country"]

            row = {
                "ip": address,
                "org": address_org,
                "asn": address_asn,
                "country": address_country,
            }

            if args.abuseipdb_api_key:
                print(f"→ Looking up {address} in AbuseIPDB")

                # build AbuseIPDB.com request URL for current address
                # see: https://docs.abuseipdb.com/#check-endpoint
                request_url = "https://api.abuseipdb.com/api/v2/check"
                request_headers = {"Key": args.abuseipdb_api_key}
                request_params = {"ipAddress": address, "maxAgeInDays": 90}

                request = requests.get(
                    request_url, headers=request_headers, params=request_params
                )

                if args.debug and request.from_cache:
                    sys.stderr.write(Fore.GREEN + "→ Request in cache.\n" + Fore.RESET)

                # if request status 200 OK
                if request.status_code == requests.codes.ok:
                    data = request.json()

                    abuseConfidenceScore = data["data"]["abuseConfidenceScore"]

                    print(f"→ {address} has score: {abuseConfidenceScore}")

                    row.update({"abuseConfidenceScore": abuseConfidenceScore})

            writer.writerow(row)

        # check if we hit IPAPI's rate limit
        elif request.status_code == 429:
            sys.stderr.write(Fore.RED + "Error: hit IPAPI rate limit.\n" + Fore.RESET)
            exit(1)
        # if request status not 200 OK
        else:
            sys.stderr.write(
                Fore.RED
                + f"Error: request failed ({request.status_code}).\n"
                + Fore.RESET
            )
            exit(1)

    # close output file before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output file before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the public IPAPI.co API for information associated with a list of IP addresses from a text file."
)
parser.add_argument(
    "-d",
    "--debug",
    help="Print debug messages to standard error (stderr).",
    action="store_true",
)
parser.add_argument(
    "-i",
    "--input-file",
    help="File name containing IP addresses to resolve.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-k",
    "--abuseipdb-api-key",
    help="AbuseIPDB.com API key if you want to check whether IPs have been reported.",
)
parser.add_argument(
    "-o",
    "--output-file",
    help="File name to save CSV output.",
    required=True,
    type=argparse.FileType("w"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

read_addresses_from_file()

exit()
