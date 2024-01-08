#!/usr/bin/env python3
#
# orcid-authority-to-item.py 1.1.1
#
# Copyright Alan Orth.
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
# Map ORCID identifiers from DSpace's Solr authority core by creating new cg.creator.id
# fields in each matching item.
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install colorama psycopg2-binary requests requests-cache
#

import argparse
import signal
import sys
from datetime import timedelta

import psycopg2
import requests
import requests_cache
from colorama import Fore


def main():
    # parse the command line arguments
    parser = argparse.ArgumentParser(
        description="Map ORCID identifiers from the DSpace Solr authority core to cg.creator.id fields in each item."
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print debug messages to standard error (stderr).",
        action="store_true",
    )
    parser.add_argument("-db", "--database-name", help="Database name", required=True)
    parser.add_argument(
        "-u", "--database-user", help="Database username", required=True
    )
    parser.add_argument(
        "-p", "--database-pass", help="Database password", required=True
    )
    parser.add_argument(
        "-s",
        "--solr-url",
        help="URL of Solr application",
        default="http://localhost:8080/solr",
    )
    args = parser.parse_args()

    # set the signal handler for SIGINT (^C) so we can exit cleanly
    signal.signal(signal.SIGINT, signal_handler)

    # get all ORCID identifiers from Solr authority core
    read_identifiers_from_solr(args)


# query DSpace's authority Solr core for authority IDs with ORCID identifiers
def read_identifiers_from_solr(args):
    # simple query from the 'authority' collection 2000 rows at a time (default is 1000)
    solr_query_params = {"q": "orcid_id:*", "wt": "json", "rows": 2000}

    solr_url = args.solr_url + "/authority/select"

    res = requests.get(solr_url, params=solr_query_params)

    if args.debug:
        numFound = res.json()["response"]["numFound"]
        sys.stderr.write(
            Fore.GREEN
            + "Total number of Solr records with ORCID iDs: {0}\n".format(
                str(numFound) + Fore.RESET
            )
        )

    # initialize an empty dictionary for authorities
    # format will be: {'d7ef744b-bbd4-4171-b449-00e37e1b776f': '0000-0002-3476-272X', ...}
    authorities = {}

    docs = res.json()["response"]["docs"]
    # iterate over results and add ORCID iDs that aren't already in the list
    # for example, we had 1600 ORCID iDs in Solr, but only 600 are unique
    for doc in docs:
        if doc["id"] not in authorities:
            authorities.update({doc["id"]: doc["orcid_id"]})

    add_orcid_identifiers(args, authorities)


# Query ORCID's public API for names associated with an identifier. Prefers to use
# the "credit-name" field if it is present, otherwise will default to using the
# "given-names" and "family-name" fields.
def resolve_orcid_identifier(args, orcid):
    # ORCID API endpoint, see: https://pub.orcid.org
    orcid_api_base_url = "https://pub.orcid.org/v2.1/"
    orcid_api_endpoint = "/person"

    # fetch names associated with an ORCID identifier from the ORCID API
    if args.debug:
        sys.stderr.write(
            Fore.GREEN
            + "Looking up the names associated with ORCID iD: {0}\n".format(orcid)
            + Fore.RESET
        )

    # enable transparent request cache with thirty-day expiry
    expire_after = timedelta(days=30)

    # cache HTTP 200 and 404 responses, because ORCID uses HTTP 404 when an identifier doesn't exist
    requests_cache.install_cache(
        "requests-cache", expire_after=expire_after, allowable_codes=(200, 404)
    )

    # build request URL for current ORCID ID
    request_url = orcid_api_base_url + orcid.strip() + orcid_api_endpoint

    # ORCID's API defaults to some custom format, so tell it to give us JSON
    request = requests.get(request_url, headers={"Accept": "application/json"})

    # prune old cache entries
    requests_cache.delete()

    # Check the request status
    if request.status_code == requests.codes.ok:
        # read response JSON into data
        data = request.json()

        # make sure name element is not null
        if data["name"]:
            # prefer credit-name if present and not blank
            if (
                data["name"]["credit-name"]
                and data["name"]["credit-name"]["value"] != ""
            ):
                line = data["name"]["credit-name"]["value"]
            # otherwise use given-names + family-name
            # make sure given-names is not null
            elif data["name"]["given-names"]:
                line = data["name"]["given-names"]["value"]
                # make sure family-name is not null
                if data["name"]["family-name"]:
                    line = line + " " + data["name"]["family-name"]["value"]
                else:
                    if args.debug:
                        sys.stderr.write(
                            Fore.YELLOW
                            + "Warning: ignoring null family-name element.\n"
                            + Fore.RESET
                        )
        else:
            if args.debug:
                sys.stderr.write(
                    Fore.YELLOW
                    + "Warning: skipping identifier with null name element.\n\n"
                    + Fore.RESET
                )
    # HTTP 404 means that the API url or identifier was not found. If the
    # API URL is correct, let's assume that the identifier was not found.
    elif request.status_code == 404:
        if args.debug:
            sys.stderr.write(
                Fore.YELLOW
                + "Warning: skipping missing identifier (API request returned HTTP 404).\n\n"
                + Fore.RESET
            )
    else:
        sys.stderr.write(Fore.RED + "Error: request failed.\n" + Fore.RESET)
        exit(1)

    return line


def add_orcid_identifiers(args, authorities):
    # connect to database
    try:
        conn_string = "dbname={0} user={1} password={2} host=localhost".format(
            args.database_name, args.database_user, args.database_pass
        )
        conn = psycopg2.connect(conn_string)

        if args.debug:
            sys.stderr.write(Fore.GREEN + "Connected to the database.\n" + Fore.RESET)
    except psycopg2.OperationalError:
        sys.stderr.write(Fore.RED + "Unable to connect to the database.\n" + Fore.RESET)
        exit(1)

    # iterate over all authorities
    for authority_id in authorities:
        # save orcid for current authority a little more cleanly
        orcid = authorities[authority_id]

        # get name associated with this orcid identifier
        name = resolve_orcid_identifier(args, orcid)
        creator = "{0}: {1}".format(name, orcid)

        if args.debug:
            sys.stderr.write(
                Fore.GREEN
                + "Processing authority ID {0} with ORCID iD: {1}\n".format(
                    authority_id, orcid
                )
                + Fore.RESET
            )

        with conn:
            # cursor will be closed after this block exits
            # see: http://initd.org/psycopg/docs/usage.html#with-statement
            with conn.cursor() as cursor:
                # find all metadata records with this authority id
                # resource_type_id 2 is item metadata, metadata_field_id 3 is author
                sql = "SELECT resource_id, place FROM metadatavalue WHERE resource_type_id=2 AND metadata_field_id=3 AND authority=%s"
                # remember that tuples with one item need a comma after them!
                cursor.execute(sql, (authority_id,))
                records_with_authority = cursor.fetchall()

                if len(records_with_authority) >= 0:
                    if args.debug:
                        sys.stderr.write(
                            Fore.GREEN
                            + "Checking {0} items for authority ID {1}.\n".format(
                                len(records_with_authority), authority_id
                            )
                            + Fore.RESET
                        )

                    # iterate over results for current authority_id to add cg.creator.id metadata
                    for record in records_with_authority:
                        resource_id = record[0]
                        # author name and orcid identifier
                        text_value = creator
                        place = record[1]
                        confidence = -1

                        # get the metadata_field_id for cg.creator.id field
                        sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=2 AND element='creator' AND qualifier='id'"
                        cursor.execute(sql)
                        metadata_field_id = cursor.fetchall()[0]

                        # first, check if there is an existing cg.creator.id here (perhaps the script crashed before?)
                        # resource_type_id 2 is item metadata
                        sql = "SELECT * from metadatavalue WHERE resource_id=%s AND metadata_field_id=%s AND text_value=%s AND place=%s AND confidence=%s AND resource_type_id=2"
                        cursor.execute(
                            sql,
                            (
                                resource_id,
                                metadata_field_id,
                                text_value,
                                place,
                                confidence,
                            ),
                        )
                        records_with_orcid = cursor.fetchall()

                        if len(records_with_orcid) == 0:
                            print(
                                "Adding ORCID identifier to item {0}: {1}".format(
                                    resource_id, creator
                                )
                            )

                            # metadatavalue IDs come from a PostgreSQL sequence that increments when you call it
                            cursor.execute("SELECT nextval('metadatavalue_seq')")
                            metadata_value_id = cursor.fetchone()[0]

                            sql = "INSERT INTO metadatavalue (metadata_value_id, resource_id, metadata_field_id, text_value, place, confidence, resource_type_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                            cursor.execute(
                                sql,
                                (
                                    metadata_value_id,
                                    resource_id,
                                    metadata_field_id,
                                    text_value,
                                    place,
                                    confidence,
                                    2,
                                ),
                            )
                        else:
                            if args.debug:
                                sys.stderr.write(
                                    Fore.GREEN
                                    + "Item {0} already has an ORCID identifier for {1}.\n".format(
                                        resource_id, creator
                                    )
                                    + Fore.RESET
                                )

    if args.debug:
        sys.stderr.write(Fore.GREEN + "Disconnecting from database.\n" + Fore.RESET)

    # close the database connection before leaving
    conn.close()


def signal_handler(signal, frame):
    sys.exit(1)


if __name__ == "__main__":
    main()
