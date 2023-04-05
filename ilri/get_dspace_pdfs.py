#!/usr/bin/env python3
#
# get_dspace_pdfs.py 0.0.2
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the CGSpace REST API for bitstreams from a list of handles and then
# downloads them if they are PDFs. Input file is hardcoded at /tmp/handles.txt
# and should have one handle per line, for example:
#
#   10568/93010
#   10568/75869
#
# I generated the list of handles by extracting them from the results of an
# OpenSearch query where the user had asked for all items matching the term
# "trade off" in the WLE community:
#
#   $ http 'https://cgspace.cgiar.org/open-search/discover?scope=10568%2F34494&query=trade+off&rpp=100&start=0' User-Agent:'curl' > /tmp/wle-trade-off-page1.xml
#   $ xmllint --xpath '//*[local-name()="entry"]/*[local-name()="id"]/text()' /tmp/wle-trade-off-page1.xml >> /tmp/ids.txt
#   # ... and on and on for each page of results...
#   $ sort -u /tmp/ids.txt > /tmp/ids-sorted.txt
#   $ grep -oE '[0-9]+/[0-9]+' /tmp/ids.txt > /tmp/handles.txt
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama requests
#

import logging
import os.path

import requests
from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)


def resolve_bitstreams(handle):
    # strip the handle because it has a line feed (%0A)
    url = f"{rest_base_url}/{rest_handle_endpoint}/{handle.strip()}"
    request_params = {"expand": "bitstreams"}
    request_headers = {"user-agent": rest_user_agent, "Accept": "application/json"}
    response = requests.get(url, params=request_params, headers=request_headers)

    if response.status_code == 200:
        bitstreams = response.json()["bitstreams"]

        if len(bitstreams) > 0:
            pdf_bitstream_ids = list()

            for bitstream in bitstreams:
                if bitstream["format"] == "Adobe PDF":
                    pdf_bitstream_ids.append(bitstream["uuid"])

            if len(pdf_bitstream_ids) > 0:
                download_bitstreams(pdf_bitstream_ids)

    return


def download_bitstreams(pdf_bitstream_ids):
    import re

    for pdf_bitstream_id in pdf_bitstream_ids:
        url = f"{rest_base_url}/{rest_bitstream_endpoint}/{pdf_bitstream_id}/retrieve"
        request_headers = {
            "user-agent": rest_user_agent,
        }

        # do a HEAD request first to get the filename from the content disposition header
        # See: https://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
        response = requests.head(url, headers=request_headers)

        if response.status_code == 200:
            content_disposition = response.headers["content-disposition"]
            filename = re.findall("filename=(.+)", content_disposition)[0]
            # filenames in the header have quotes so let's strip them in a super hacky way
            filename_stripped = filename.strip('"')
            logger.info(f"filename: {filename_stripped}")

        # check if file exists
        if os.path.isfile(filename_stripped):
            logger.warning(
                Fore.YELLOW
                + "> {} already downloaded.".format(filename_stripped)
                + Fore.RESET
            )
        else:
            logger.info(
                Fore.GREEN
                + "> Downloading {}...".format(filename_stripped)
                + Fore.RESET
            )

            response = requests.get(
                url, headers={"user-agent": rest_user_agent}, stream=True
            )
            if response.status_code == 200:
                with open(filename_stripped, "wb") as fd:
                    for chunk in response:
                        fd.write(chunk)
            else:
                logger.error(
                    Fore.RED
                    + "> Download failed, I will try again next time."
                    + Fore.RESET
                )

    return


rest_base_url = "https://cgspace.cgiar.org/rest"
rest_handle_endpoint = "handle"
rest_bitstream_endpoint = "bitstreams"
rest_user_agent = "curl"

logger.setLevel(logging.INFO)

with open("/tmp/handles.txt", "r") as fd:
    handles = fd.readlines()

for handle in handles:
    resolve_bitstreams(handle)
