#!/usr/bin/env python3
#
# get_pdfs_dspace.py 0.0.3
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the DSpace 7 API for bitstreams from a list of handles and then down-
# loads them if they are PDFs. Input file is hardcoded at /tmp/handles.txt and
# should have one handle per line, for example:
#
#   10568/93010
#   10568/75869
#   https://hdl.handle.net/10568/33365
#
# For now the Handles should belong to one repository, with the REST API URL
# hardcoded in this script.

import logging
import os
import re

from colorama import Fore
from dspace_rest_client.client import DSpaceClient
from dspace_rest_client.models import Bitstream, Bundle, Item

# Create a local logger instance
logger = logging.getLogger(__name__)


def resolve_bitstreams(handle):
    # This returns a list, even if it is only one item
    items = d.search_objects(query=f"handle:{handle}", dso_type="item")

    # We should only have one result for an exact Handle query!
    if len(items) == 1:
        bundles = d.get_bundles(parent=items[0])
        for bundle in bundles:
            if bundle.name == "ORIGINAL":
                bitstreams = d.get_bitstreams(bundle=bundle)

                pdf_bitstreams = []
                for bitstream in bitstreams:
                    # DSpace Python client doesn't have mime currently
                    if ".pdf" in bitstream.name:
                        pdf_bitstreams.append(bitstream)

                # Temporary so we don't have to worry about handling multiple PDFs
                if len(pdf_bitstreams) == 1:
                    download_bitstreams(handle, pdf_bitstreams)

    return


def download_bitstreams(handle, pdf_bitstreams):
    for pdf_bitstream in pdf_bitstreams:
        filename = handle.replace("/", "-") + ".pdf"

        # check if file exists
        if os.path.isfile(filename):
            logger.debug(f"{Fore.YELLOW}> {filename} already downloaded.{Fore.RESET}")
        else:
            logger.info(f"{Fore.GREEN}> Trying to download {filename}...{Fore.RESET}")

            r = d.download_bitstream(pdf_bitstream.uuid)

            try:
                with open(filename, "wb") as fd:
                    fd.write(r.content)
            except AttributeError:
                # The item may be locked on DSpace, which causes the content to be None
                logger.error(
                    f"{Fore.RED}> Failed to download {filename}...{Fore.RESET}"
                )

                os.remove(filename)

                pass

    return


dspace_rest_api = "https://cgspace.cgiar.org/server/api"

# Set local logging level to INFO
logger.setLevel(logging.INFO)
# Set the global log format to display just the message without the log level
logging.basicConfig(format="%(message)s")

d = DSpaceClient(api_endpoint=dspace_rest_api)

with open("/tmp/handles.txt", "r") as fd:
    handles = fd.readlines()

for handle in handles:
    # Extract Handle from URI if this is the format
    if "https://hdl.handle.net/" in handle:
        handle = handle.split("https://hdl.handle.net/")[1]

    # strip the handle in case it has a line feed (%0A)
    handle = handle.strip()

    logger.info(f"Checking for PDF bitstreams in {handle}")

    resolve_bitstreams(handle)
