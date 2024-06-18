#!/usr/bin/env python3
#
# post_bitstreams.py 0.1.3
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
# TODO: allow overwriting by bitstream description
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama requests
#

import argparse
import csv
import logging
import os.path
import signal
import sys

import requests
from colorama import Fore

# Create a local logger instance for this module. We don't do any configuration
# because this module might be used elsewhere that will have its own logging
# configuration.
logger = logging.getLogger(__name__)


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

    logger.info("Logging in...")

    try:
        request = requests.post(rest_login_endpoint, headers=headers, data=data)
    except requests.ConnectionError:
        logger.error(
            Fore.RED
            + f"> Could not connect to REST API: {args.request_url}"
            + Fore.RESET
        )

        sys.exit(1)

    if request.status_code != requests.codes.ok:
        logger.error(Fore.RED + "> Login failed." + Fore.RESET)

        sys.exit(1)

    try:
        jsessionid = request.cookies["JSESSIONID"]
    except KeyError:
        logger.error(
            Fore.RED
            + f"Login failed (HTTP {request.status_code}): missing JESSSIONID cookie in response...?"
            + Fore.RESET
        )

        sys.exit(1)

    logger.debug(
        Fore.GREEN + f"Login successful, new JSESSIONID: {jsessionid}" + Fore.RESET
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

    logger.debug(f"Checking status of existing session: {jsessionid}" + Fore.RESET)

    try:
        request = requests.get(request_url, headers=headers, cookies=cookies)
    except requests.ConnectionError:
        logger.error(
            Fore.RED
            + f"> Could not connect to REST API: {args.request_url}"
            + Fore.RESET
        )

        sys.exit(1)

    if request.status_code == requests.codes.ok:
        if not request.json()["authenticated"]:
            logger.warning(Fore.RED + f"Session expired: {jsessionid}" + Fore.RESET)

            return False
    else:
        logger.error(Fore.RED + "Error checking session status." + Fore.RESET)

        return False

    logger.debug(Fore.GREEN + f"Session valid: {jsessionid}" + Fore.RESET)

    return True


def check_item(item_id: str, bundle: str):
    """Check if the item already has bitstreams.

    Equivalent to the following request with httpie or curl:

       $ http 'http://localhost:8080/rest/items/804351af-64eb-4e4a-968f-4d3be61358a8?expand=bitstreams,metadata' \
            Cookie:JSESSIONID=B3B9C82F257BCE1773E6FB1EA5ACD774

    By default this will return True if the item has any bitstreams in the named
    bundle and False if the bundle is empty. If the user has asked to overwrite
    bitstreams then we will do that first, and return False once the bundle is
    empty.

    :param item_id: uuid of item in the DSpace repository.
    :returns: bool
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
        logger.error(
            Fore.RED
            + f"> Could not connect to REST API: {args.request_url}"
            + Fore.RESET
        )

        sys.exit(1)

    # If the item doesn't exist, return True early so we don't try to upload a
    # bitstream
    if request.status_code == 404:
        logger.warning(Fore.RED + "Item not found." + Fore.RESET)
        return True

    if request.status_code == requests.codes.ok:
        data = request.json()

        # List comprehension to filter out bitstreams that belong to the bundle
        # we're interested in
        bitstreams_in_bundle = [
            bitstream
            for bitstream in data["bitstreams"]
            if bitstream["bundleName"] == bundle
        ]

        if len(bitstreams_in_bundle) == 0:
            # Return False, meaning the item does not have a bitstream in this bundle yet
            return False

        # We have bitstreams, so let's see if the user wants to overwrite them
        if args.overwrite_format:
            bitstreams_to_overwrite = [
                bitstream
                for bitstream in bitstreams_in_bundle
                if bitstream["format"] in args.overwrite_format
            ]

            # Item has bitstreams, but none matching our overwrite format. Let's
            # err on the side of caution and return True so that we don't upload
            # another one into the bundle.
            if len(bitstreams_to_overwrite) == 0:
                logger.debug(
                    "Existing bitstreams, but none matching our overwrite formats."
                )

                return True

            for bitstream in bitstreams_to_overwrite:
                if args.dry_run:
                    logger.info(
                        Fore.YELLOW
                        + f"> (DRY RUN) Deleting bitstream: {bitstream['name']} ({bitstream['uuid']})"
                        + Fore.RESET
                    )

                else:
                    if delete_bitstream(bitstream["uuid"]):
                        logger.info(
                            Fore.YELLOW
                            + f"> Deleted bitstream: {bitstream['name']} ({bitstream['uuid']})"
                            + Fore.RESET
                        )

            # Return False, indicating there are no bitstreams in this bundle
            return False
        else:
            logger.debug(
                f"> Skipping item with existing bitstream(s) in {bundle} bundle"
            )

            return True

    # If we get here, assume the item has a bitstream and return True so we
    # don't upload another.
    return True


def delete_bitstream(bitstream_id: str):
    """Delete a bitstream.

    Equivalent to the following request with httpie or curl:

       $ http DELETE 'http://localhost:8080/rest/bitstreams/fca0fd2a-630e-4a34-b260-f645c8f2b027' \
            Cookie:JSESSIONID=B3B9C82F257BCE1773E6FB1EA5ACD774

    :param bitstream_id: uuid of bitstream in the DSpace repository.
    :returns: bool
    """

    request_url = f"{rest_bitstreams_endpoint}/{bitstream_id}"
    headers = {"user-agent": user_agent}
    cookies = {"JSESSIONID": jsessionid}

    try:
        request = requests.delete(request_url, headers=headers, cookies=cookies)
    except requests.ConnectionError:
        logger.error(
            Fore.RED
            + f"> Could not connect to REST API: {args.request_url}"
            + Fore.RESET
        )

        sys.exit(1)

    if request.status_code == requests.codes.ok:
        return True
    else:
        return False


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
        logger.error(
            Fore.RED + f"> Could not connect to REST API: {request_url}" + Fore.RESET
        )

        sys.exit(1)
    except FileNotFoundError:
        logger.error(Fore.RED + f"> Could not open {filename}" + Fore.RESET)

        return False

    if request.status_code == requests.codes.ok:
        return True
    else:
        logger.error(Fore.RED + f"> Error uploading file: {filename}" + Fore.RESET)

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
        "-n",
        "--dry-run",
        help="Only print changes that would be made.",
        action="store_true",
    )
    parser.add_argument(
        "-u",
        "--rest-url",
        help="URL of the DSpace 6.x REST API.",
        default="http://localhost:8080/rest",
    )
    parser.add_argument("-e", "--user", help="Email address of administrator user.")
    parser.add_argument(
        "--overwrite-format",
        help="Bitstream formats to overwrite. Specify multiple formats separated by a space. Use this carefully, test with dry run first!",
        choices=["PNG", "JPEG", "GIF", "Adobe PDF", "WebP"],
        action="extend",
        nargs="+",
    )
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
    args = parser.parse_args()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Since we're running interactively we can set the preferred log format for
    # the logging module during this invocation.
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    # DSpace 6.x REST API base URL and endpoints
    rest_base_url = args.rest_url
    rest_login_endpoint = f"{rest_base_url}/login"
    rest_status_endpoint = f"{rest_base_url}/status"
    rest_items_endpoint = f"{rest_base_url}/items"
    rest_bitstreams_endpoint = f"{rest_base_url}/bitstreams"
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

        logger.debug(f"Opened {args.csv_file.name}")
    except FileNotFoundError:
        logger.error(Fore.RED + f"Could not open {args.csv_file.name}" + Fore.RESET)

    # Check if the required fields exist in the CSV
    for field in ["id", "filename", "bundle"]:
        if field not in reader.fieldnames:
            logger.error(
                Fore.RED
                + f"Expected field {field} does not exist in the CSV."
                + Fore.RESET
            )

            sys.exit(1)

    for row in reader:
        item_id = row["id"]
        bundle = row["bundle"]

        # Check if this item already has a bitstream in this bundle (check_item
        # returns True if the bundle already has a bitstream).
        logger.info(f"{item_id}: checking for existing bitstreams in {bundle} bundle")

        if not check_item(item_id, bundle):
            # Check if there is a description for this filename
            try:
                filename = row["filename"].split("__description:")[0]
                description = row["filename"].split("__description:")[1]
            except IndexError:
                filename = row["filename"].split("__description:")[0]
                description = False

            if not os.path.isfile(filename):
                logger.info(
                    f"{Fore.YELLOW}> File not found, skipping: {filename}{Fore.RESET}"
                )

                continue

            if args.dry_run:
                logger.info(
                    f"{Fore.YELLOW}> (DRY RUN) Uploading file: {filename}{Fore.RESET}"
                )
            else:
                if upload_file(item_id, bundle, filename, description):
                    logger.info(
                        f"{Fore.YELLOW}> Uploaded file: {filename} ({bundle}){Fore.RESET}"
                    )
