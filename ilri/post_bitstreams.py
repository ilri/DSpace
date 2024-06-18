#!/usr/bin/env python3
#
# post_bitstreams.py 0.2.0
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
# use http://localhost:8080/server/api).
#
# TODO: fix overwriting by mime
# TODO: allow overwriting by bitstream description

import argparse
import csv
import logging
import os.path
import signal
import sys

from colorama import Fore
from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Bitstream, Bundle, Item

# Create a local logger instance for this module. We don't do any configuration
# because this module might be used elsewhere that will have its own logging
# configuration.
logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    sys.exit(1)


def check_item(item_id: str, bundle_name: str):
    """Check if the item already has bitstreams.

    By default this will return True if the item has any bitstreams in the named
    bundle and False if the bundle is empty. If the user has asked to overwrite
    bitstreams then we will do that first, and return False once the bundle is
    empty. If there is any error along the way we return True we don't try to
    upload a bitstream.

    :param item_id: uuid of item in the DSpace repository.
    :param bundle_name: name of the target bundle.
    :returns: bool
    """

    # d.get_item() returns a requests response so we need to cast to Item
    item = Item(d.get_item(item_id).json())

    if isinstance(item, Item) and item.uuid is not None:
        logger.debug("> Success")
    else:
        logger.debug(f"{Fore.RED}> Failed to find item {item.uuid}{Fore.RESET}")

        return True

    bundle = None

    # Try to find existing bundle
    for item_bundle in d.get_bundles(parent=item):
        if item_bundle.name == bundle_name:
            bundle = item_bundle

            if isinstance(bundle, Bundle) and bundle.uuid is not None:
                logger.debug(f"> Found {bundle.name} bundle: {bundle.uuid}")
            else:
                logger.debug(
                    f"{Fore.RED}> Error with {bundle.name} bundle: {bundle.uuid}{Fore.RESET}"
                )

                return True

    # Create new bundle if we didn't find one
    if bundle is None:
        bundle = d.create_bundle(parent=item, name=bundle_name)
        if isinstance(bundle, Bundle) and bundle.uuid is not None:
            logger.debug(
                f"{Fore.YELLOW}> Created {bundle.name} bundle: {bundle.uuid}{Fore.RESET}"
            )

            return False
        else:
            logger.debug(
                f"{Fore.RED}> Failed to create {bundle_name} bundle{Fore.RESET}"
            )

            return True

    bitstreams_in_bundle = d.get_bitstreams(bundle=bundle)

    if len(bitstreams_in_bundle) == 0:
        # Return False, meaning the item does not have a bitstream in this bundle yet
        return False

    # We have bitstreams, so let's see if the user wants to overwrite them
    # if args.overwrite_format:
    #    bitstreams_to_overwrite = [
    #        bitstream
    #        for bitstream in bitstreams_in_bundle
    #        if bitstream["format"] in args.overwrite_format
    #    ]

    #    # Item has bitstreams, but none matching our overwrite format. Let's
    #    # err on the side of caution and return True so that we don't upload
    #    # another one into the bundle.
    #    if len(bitstreams_to_overwrite) == 0:
    #        logger.debug(
    #            "Existing bitstreams, but none matching our overwrite formats."
    #        )

    #        return True

    #    for bitstream in bitstreams_to_overwrite:
    #        if args.dry_run:
    #            logger.info(
    #                Fore.YELLOW
    #                + f"> (DRY RUN) Deleting bitstream: {bitstream['name']} ({bitstream['uuid']})"
    #                + Fore.RESET
    #            )

    #        else:
    #            if delete_bitstream(bitstream["uuid"]):
    #                logger.info(
    #                    Fore.YELLOW
    #                    + f"> Deleted bitstream: {bitstream['name']} ({bitstream['uuid']})"
    #                    + Fore.RESET
    #                )

    #    # Return False, indicating there are no bitstreams in this bundle
    #    return False
    # else:
    #    logger.debug(f"> Skipping item with existing bitstream(s) in {bundle} bundle")

    #    return True

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

    if request.status_code == requests.codes.ok:
        return True
    else:
        return False


def upload_file(item_id: str, bundle_name: str, filename: str, description):
    """Upload a file to an existing item in the DSpace repository.

    :param item_id: UUID of item to post the file to.
    :param bundle: Name of the bundle to upload bitstream to, ie ORIGINAL, THUMBNAIL, etc (will be created if it doesn't exist).
    :param filename: Name of the file to upload (must exist in the same directory as the script).
    :param description: Bitstream description for this file.
    :returns: bool
    """

    bitstream_metadata = {
        "dc.description": [
            {
                "value": f"{description}",
                "language": "en",
                "authority": None,
                "confidence": -1,
                "place": 0,
            }
        ]
    }

    # Ugh, get the Item and Bundle again... since we already got these in the
    # check_item I am going to do no error handling here for now.
    item = Item(d.get_item(item_id).json())
    for item_bundle in d.get_bundles(parent=item):
        if item_bundle.name == bundle_name:
            bundle = item_bundle

            break

    # Hardcoding mime for now... ugh.
    new_bitstream = d.create_bitstream(
        bundle=bundle,
        name=filename,
        path=filename,
        mime="application/pdf",
        metadata=bitstream_metadata,
    )

    if isinstance(new_bitstream, Bitstream) and new_bitstream.uuid is not None:
        return True
    else:
        return False


if __name__ == "__main__":
    # Set the signal handler for SIGINT (^C)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Post bitstreams to existing items in a DSpace 7.x repository."
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
        help="URL of the DSpace 7.x REST API.",
        default="http://localhost:8080/server/api",
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
    args = parser.parse_args()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Since we're running interactively we can set the preferred log format for
    # the logging module during this invocation.
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    d = DSpaceClient(
        api_endpoint=args.rest_url, username=args.user, password=args.password
    )

    authenticated = d.authenticate()
    if not authenticated:
        logger.error(f"{Fore.RED}Error logging in! Giving up.{Fore.RESET}")
        sys.exit(1)

    try:
        # Open the CSV
        reader = csv.DictReader(args.csv_file)

        logger.debug(f"Opened {args.csv_file.name}")
    except FileNotFoundError:
        logger.error(f"{Fore.RED}Could not open {args.csv_file.name}{Fore.RESET}")

    # Check if the required fields exist in the CSV
    for field in ["id", "filename", "bundle"]:
        if field not in reader.fieldnames:
            logger.error(
                f"{Fore.RED}Expected field {field} does not exist in the CSV.{Fore.RESET}"
            )

            sys.exit(1)

    for row in reader:
        item_id = row["id"]
        bundle_name = row["bundle"]

        # Check if this item already has a bitstream in this bundle (check_item
        # returns True if the bundle already has a bitstream).
        logger.info(
            f"{item_id}: checking for existing bitstreams in {bundle_name} bundle"
        )

        if not check_item(item_id, bundle_name):
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
                if upload_file(item_id, bundle_name, filename, description):
                    logger.info(
                        f"{Fore.YELLOW}> Uploaded file: {filename} ({bundle_name}){Fore.RESET}"
                    )
                else:
                    logger.error(
                        f"{Fore.RED}> Error uploading file: {filename}{Fore.RESET}"
                    )
