#!/usr/bin/env python3
#
# post-ciat-pdfs.py 0.0.1
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# A script to read item IDs and URLs from a CSV file and update existing items
# in a DSpace repository via the REST API. Developed when we had a corporate
# website with thousands of PDFs go offline and wanted to upload the PDFs to
# their existing metadata-only accessions in our respository. Specify an email
# and for a DSpace user with administrator privileges when running:
#
#   $ ./post-ciat-pdfs.py -i items.csv -e me@example.com -p 'fuu!'
#
# The CSV input file should have DSpace item IDs (UUID) and URLs, ie:
#
#   id,url
#   804351af-64eb-4e4a-968f-4d3be61358a8,http://example.com/library/file1.pdf
#   82b8c92c-fd6e-4b30-a704-5fbdc1cc6d1c,http://example.com/library/file2.pdf
#
# You can optionally specify the URL of a DSpace REST application (default is to
# use http://localhost:8080/rest). If your CSV file has a large number of URLs
# to download you can run it first in download-only mode with the "-w" option.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama requests
#

import argparse
import csv
import os.path
import signal
import sys
from urllib.parse import unquote, urlparse

import requests
from colorama import Fore


def signal_handler(signal, frame):
    sys.exit(1)


def login(user: str, password: str):
    """Log into the DSpace REST API.

    Equivalent to the following request with httpie or curl:

        $ http -f POST http://localhost:8080/rest/login email=aorth@fuuu.com password='fuuuuuu'

    :param user: email of user with permissions to update the item (should probably be an admin).
    :param password: password of user.
    :returns: JSESSION value for the session.
    """

    headers = {"user-agent": user_agent}
    data = {"email": args.user, "password": args.password}

    print("Logging in...")

    try:
        request = requests.post(rest_login_endpoint, headers=headers, data=data)
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED
            + f" Could not connect to REST API: {rest_login_endpoint}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code != requests.codes.ok:
        sys.stderr.write(Fore.RED + " Login failed.\n" + Fore.RESET)

        exit(1)

    jsessionid = request.cookies["JSESSIONID"]

    if args.debug:
        sys.stderr.write(
            Fore.GREEN + f" Logged in using JSESSIONID: {jsessionid}\n" + Fore.RESET
        )

    return jsessionid


def check_session(jsessionid: str):
    """Check the authentication status of the specified JSESSIONID.

    :param jsessionid: JSESSIONID value for a previously authenticated session.
    :returns: bool
    """

    request_url = rest_status_endpoint
    headers = {"user-agent": user_agent, "Accept": "application/json"}
    cookies = {"JSESSIONID": jsessionid}

    try:
        request = requests.get(request_url, headers=headers, cookies=cookies)
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED
            + f" Could not connect to REST API: {args.request_url}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code == requests.codes.ok:
        if not request.json()["authenticated"]:
            sys.stderr.write(
                Fore.RED + f" Session expired: {jsessionid}\n" + Fore.RESET
            )

            return False
    else:
        sys.stderr.write(Fore.RED + " Error checking session status.\n" + Fore.RESET)

        return False

    return True


def url_to_filename(url: str):
    """Return filename from a URL.

    Uses the following process to extract the filename from a given URL:

        1. Split path component on slash like ['docs', 'file.pdf']
        2. Take last element ([-1])
        3. URL unencode using unquote() so we don't have "file%20name.pdf"

    :param url: URL of a PDF file to download, for example "https://example.com/docs/file.pdf"
    :returns: filename, for example "file.pdf"
    """

    return unquote(urlparse(url).path.split("/")[-1])


def check_item(row: dict):
    """Check if the item already has bitstreams.

    Equivalent to the following request with httpie or curl:

       $ http 'http://localhost:8080/rest/items/804351af-64eb-4e4a-968f-4d3be61358a8?expand=bitstreams,metadata' \
            Cookie:JSESSIONID=B3B9C82F257BCE1773E6FB1EA5ACD774

    To be safe, and to save myself from having to write extra logic, we only
    want to upload files to items that don't already have one.

    :param row: row from the CSV file containing the item ID and URL of a file to download.
    """

    url = row["url"]
    item_id = row["id"]

    request_url = f"{rest_items_endpoint}/{item_id}"
    headers = {"user-agent": user_agent}
    # Not strictly needed here for permissions, but let's give the session ID
    # so that we don't allocate unecessary resources on the server.
    cookies = {"JSESSIONID": jsessionid}
    request_params = {"expand": "bitstreams,metadata"}

    try:
        request = requests.get(
            request_url, headers=headers, cookies=cookies, params=request_params
        )
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED
            + f"  Could not connect to REST API: {args.request_url}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code == requests.codes.ok:
        data = request.json()

        if len(data["bitstreams"]) == 0:
            filename = url_to_filename(url)

            # Find the item type so we can use it as the bitstream description.
            # Note that we don't check for null or empty here.
            for field in data["metadata"]:
                if field["key"] == "dcterms.type":
                    item_type = field["value"]

            if args.debug:
                print(f"{item_id}: uploading {filename}")

            if upload_file(item_id, filename, item_type):
                print(Fore.YELLOW + f"{item_id}: uploaded {filename}" + Fore.RESET)
        else:
            if args.debug:
                sys.stderr.write(
                    f"{item_id}: skipping item with existing bitstream(s)\n"
                )


def download_file(url: str):
    filename = url_to_filename(url)

    request_headers = {"user-agent": user_agent}

    # Check if file already exists
    if os.path.isfile(filename):
        if args.debug:
            print(f"> {filename} already downloaded.")
    else:
        print(f"> Downloading {filename}...")

        response = requests.get(row["url"], headers=request_headers, stream=True)
        if response.status_code == 200:
            with open(filename, "wb") as fd:
                for chunk in response:
                    fd.write(chunk)
        else:
            print(
                Fore.RED
                + f" > Download failed (HTTP {response.status_code})"
                + Fore.RESET
            )

            return False

    return True


def upload_file(item_id: str, filename: str, item_type: str):
    """Upload a file to an existing item in the DSpace repository.

    Equivalent to the following request with httpie or curl:

        http POST \
            'http://localhost:8080/rest/items/21c0db9d-6c35-4111-9ca1-2c1345f44e40/bitstreams?name=file.pdf&description=Book' \
            Cookie:JSESSIONID=0BDB219712F4F7DDB6055C1906F3E24B < file.pdf

    This will upload the bitstream into the item's ORIGINAL bundle.

    TODO: parameterize the bundle name so that we could upload a bunch of thumbnails.

    :param item_id: UUID of item to post the file to.
    :param filename: Name of the file to upload (must exist in the same directory as the script).
    :param item_type: Type of the item, to be used for the bitstream description.
    :returns: bool
    """

    try:
        # Open the file
        file = open(filename, "rb")
    except FileNotFoundError:
        sys.stderr.write(Fore.RED + f"  Could not open {filename}\n" + Fore.RESET)

    request_url = f"{rest_items_endpoint}/{item_id}/bitstreams"
    headers = {"user-agent": user_agent}
    cookies = {"JSESSIONID": jsessionid}
    request_params = {"name": filename, "description": item_type}

    try:
        request = requests.post(
            request_url,
            headers=headers,
            cookies=cookies,
            params=request_params,
            files={"file": file},
        )
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED + f"  Could not connect to REST API: {request_url}\n" + Fore.RESET
        )

        exit(1)

    if request.status_code == requests.codes.ok:
        file.close()

        return True
    else:
        print(Fore.RED + f"  Error uploading file: {filename}" + Fore.RESET)
        file.close()

        return False


parser = argparse.ArgumentParser(
    description="Download files and post them to existing items in a DSpace 6.x repository."
)
parser.add_argument("-d", "--debug", help="Print debug messages.", action="store_true")
parser.add_argument(
    "-u",
    "--rest-url",
    help="URL of the DSpace 6.x REST API.",
    default="http://localhost:8080/rest",
)
parser.add_argument("-e", "--user", help="Email address of administrator user.")
parser.add_argument("-p", "--password", help="Password of administrator user.")
parser.add_argument(
    "-i",
    "--csv-file",
    help="Path to CSV file",
    required=True,
    type=argparse.FileType("r", encoding="UTF-8"),
)
parser.add_argument(
    "-s", "--jsessionid", help="JESSIONID, if previously authenticated."
)
parser.add_argument(
    "-w", "--download-only", help="Only download the files.", action="store_true"
)
args = parser.parse_args()

# DSpace 6.x REST API base URL and endpoints
rest_base_url = args.rest_url
rest_login_endpoint = f"{rest_base_url}/login"
rest_status_endpoint = f"{rest_base_url}/status"
rest_items_endpoint = f"{rest_base_url}/items"
user_agent = "Alan Orth (ILRI) Python bot"

# Set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# If the user passed a session ID then we should check if it is valid first.
# Otherwise we should login and get a new session. If the user requested for
# download only mode then we skip authentication checks.
if args.jsessionid and not args.download_only:
    if check_session(args.jsessionid):
        jsessionid = args.jsessionid
    else:
        jsessionid = login(args.user, args.password)
elif not args.download_only:
    jsessionid = login(args.user, args.password)

if args.debug:
    sys.stderr.write(f"Opening {args.csv_file.name}\n")

try:
    # Open the CSV
    reader = csv.DictReader(args.csv_file)
except FileNotFoundError:
    sys.stderr.write(Fore.RED + f"  Could not open {args.csv_file.name}\n" + Fore.RESET)

# Check if the item ID and URL fields exist in the CSV
for field in ["id", "url"]:
    if field not in reader.fieldnames:
        sys.stderr.write(
            Fore.RED
            + f"Expected field {field} does not exist in the CSV.\n"
            + Fore.RESET
        )
        sys.exit(1)

for row in reader:
    if download_file(row["url"]):
        if not args.download_only:
            check_item(row)
