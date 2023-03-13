#!/usr/bin/env python3
#
# post_bitstreams.py 0.0.1
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# A script to read item IDs and filenames from a CSV file and update existing
# items in a DSpace repository via the REST API. Specify an email for a DSpace
# user with administrator privileges when running:
#
#   $ ./post_bitsreams.py -i items.csv -e me@example.com -p 'fuu!'
#
# The CSV input file should have DSpace item IDs, filenames, and bundle names,
# for example:
#
#   id,filename,bundle
#   804351af-64eb-4e4a-968f-4d3be61358a8,file1.pdf__description:Report,ORIGINAL
#   82b8c92c-fd6e-4b30-a704-5fbdc1cc6d1c,file2.pdf__description:Journal Article,ORIGINAL
#   82b8c92c-fd6e-4b30-a704-5fbdc1cc6d1c,thumbnail.png__description:libvips thumbnail,THUMBNAIL
#
# Optionally specify the bitstream description using the SAFBuilder syntax.
#
# You can optionally specify the URL of a DSpace REST application (default is to
# use http://localhost:8080/rest).
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

    request_url = rest_login_endpoint
    headers = {"user-agent": user_agent}
    data = {"email": args.user, "password": args.password}

    if not args.quiet:
        print(f"Logging in...\n")

    try:
        request = requests.post(rest_login_endpoint, headers=headers, data=data)
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED
            + f"> Could not connect to REST API: {args.request_url}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code != requests.codes.ok:
        sys.stderr.write(Fore.RED + "> Login failed.\n" + Fore.RESET)

        exit(1)

    try:
        jsessionid = request.cookies["JSESSIONID"]
    except KeyError:
        sys.stderr.write(
            Fore.RED
            + f"Login failed (HTTP {request.status_code}): missing JESSSIONID cookie in response...?\n"
            + Fore.RESET
        )

        exit(1)

    if args.debug:
        sys.stderr.write(
            Fore.GREEN + f"Logged in using JSESSIONID: {jsessionid}\n" + Fore.RESET
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
            + f"> Could not connect to REST API: {args.request_url}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code == requests.codes.ok:
        if not request.json()["authenticated"]:
            sys.stderr.write(Fore.RED + f"Session expired: {jsessionid}\n" + Fore.RESET)

            return False
    else:
        sys.stderr.write(Fore.RED + "Error checking session status.\n" + Fore.RESET)

        return False

    if args.debug:
        sys.stderr.write(Fore.GREEN + f"Session valid: {jsessionid}\n" + Fore.RESET)

    return True


def check_item(item_id: str):
    """Check if the item already has bitstreams.

    Equivalent to the following request with httpie or curl:

       $ http 'http://localhost:8080/rest/items/804351af-64eb-4e4a-968f-4d3be61358a8?expand=bitstreams,metadata' \
            Cookie:JSESSIONID=B3B9C82F257BCE1773E6FB1EA5ACD774

    To be safe, and to save myself from having to write extra logic, we only
    want to upload files to items that don't already have one.

    :param item_id: uuid of item in the DSpace repository.
    """

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
            + f"> Could not connect to REST API: {args.request_url}\n"
            + Fore.RESET
        )

        exit(1)

    if request.status_code == requests.codes.ok:
        data = request.json()

        if len(data["bitstreams"]) == 0:
            # Return False, meaning the item does not have a bistream already
            return False
        else:
            if args.debug:
                sys.stderr.write(f"> Skipping item with existing bitstream(s)\n")

            return True

    # If we get here, assume the item has a bitstream and return True so we
    # don't upload another.
    return True


def upload_file(item_id: str, bundle: str, filename: str, description):
    """Upload a file to an existing item in the DSpace repository.

    Equivalent to the following request with httpie or curl:

        http POST \
            'http://localhost:8080/rest/items/21c0db9d-6c35-4111-9ca1-2c1345f44e40/bitstreams?name=file.pdf&description=Book&bundleName=ORIGINAL' \
            Cookie:JSESSIONID=0BDB219712F4F7DDB6055C1906F3E24B < file.pdf

    :param item_id: UUID of item to post the file to.
    :param bundle: Name of the bundle to upload bitstream to, ie ORIGINAL, THUMBNAIL, etc (will be created if it doesn't exist).
    :param filename: Name of the file to upload (must exist in the same directory as the script).
    :param description: Bitstream description for this file.
    :returns: bool
    """

    request_url = f"{rest_items_endpoint}/{item_id}/bitstreams"
    headers = {"user-agent": user_agent}
    cookies = {"JSESSIONID": jsessionid}

    # Description is optional
    if description:
        request_params = {
            "name": filename,
            "bundleName": bundle,
            "description": description,
        }
    else:
        request_params = {"name": filename, "bundleName": bundle}

    try:
        with open(filename, "rb") as file:
            # I'm not sure why, but we need to use data instead of files here
            # See: https://stackoverflow.com/questions/12385179/how-to-send-a-multipart-form-data-with-requests-in-python
            # See: https://stackoverflow.com/questions/43500502/send-file-through-post-without-content-disposition-in-python
            request = requests.post(
                request_url,
                headers=headers,
                cookies=cookies,
                params=request_params,
                data=file.read(),
            )
    except requests.ConnectionError:
        sys.stderr.write(
            Fore.RED + f"> Could not connect to REST API: {request_url}\n" + Fore.RESET
        )

        exit(1)
    except FileNotFoundError:
        sys.stderr.write(Fore.RED + f"> Could not open {filename}\n" + Fore.RESET)

        return False

    if request.status_code == requests.codes.ok:
        return True
    else:
        print(Fore.RED + f"> Error uploading file: {filename}" + Fore.RESET)

        return False


if __name__ == "__main__":
    # Set the signal handler for SIGINT (^C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Post bitstreams to existing items in a DSpace 6.x repository."
    )
    parser.add_argument(
        "-d", "--debug", help="Print debug messages.", action="store_true"
    )
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
        "-q",
        "--quiet",
        help="Do not print progress messages to the screen.",
        action="store_true",
    )
    parser.add_argument(
        "-s", "--jsessionid", help="JESSIONID, if previously authenticated."
    )
    args = parser.parse_args()

    # DSpace 6.x REST API base URL and endpoints
    rest_base_url = args.rest_url
    rest_login_endpoint = f"{rest_base_url}/login"
    rest_status_endpoint = f"{rest_base_url}/status"
    rest_items_endpoint = f"{rest_base_url}/items"
    user_agent = "Alan Orth (ILRI) Python bot"

    # If the user passed a session ID then we should check if it is valid first.
    # Otherwise we should login and get a new session.
    if args.jsessionid:
        if check_session(args.jsessionid):
            jsessionid = args.jsessionid
        else:
            jsessionid = login(args.user, args.password)
    else:
        jsessionid = login(args.user, args.password)

    try:
        # Open the CSV
        reader = csv.DictReader(args.csv_file)

        if args.debug:
            sys.stderr.write(f"Opened {args.csv_file.name}\n")
    except FileNotFoundError:
        sys.stderr.write(
            Fore.RED + f"Could not open {args.csv_file.name}\n" + Fore.RESET
        )

    # Check if the required fields exist in the CSV
    for field in ["id", "filename", "bundle"]:
        if field not in reader.fieldnames:
            sys.stderr.write(
                Fore.RED
                + f"Expected field {field} does not exist in the CSV.\n"
                + Fore.RESET
            )

            sys.exit(1)

    for row in reader:
        item_id = row["id"]
        # Check if this item already has a bitstream (check_item returns True if the
        # item already has a bitstream).
        print(f"{item_id}: checking for existing bitstreams")

        if not check_item(item_id):
            # Check if there is a description for this filename
            try:
                filename = row["filename"].split("__description:")[0]
                description = row["filename"].split("__description:")[1]
            except IndexError:
                filename = row["filename"].split("__description:")[0]
                description = False

            if not args.quiet:
                print(f"> {item_id}, uploading bitstream: {filename}")

            if upload_file(item_id, row["bundle"], filename, description):
                print(
                    Fore.YELLOW + f"> {item_id}, uploaded file: {filename}" + Fore.RESET
                )
