# util.py v0.0.5
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Various helper functions for CGSpace DSpace Python scripts.
#

import gzip
import os
import re
import shutil
import sys

import psycopg
import requests
import requests_cache
from colorama import Fore


def field_name_to_field_id(cursor, metadata_field: str):
    """Return the metadata_field_id for a given metadata field.

    TODO: handle case where schema doesn't exist
    TODO: handle case where metadata field doesn't exist

    :param cursor: a psycopg cursor with an active database session.
    :param metadata_field: the metadata field, for example "dcterms.title".
    :returns int
    """

    if len(metadata_field.split(".")) == 3:
        schema, element, qualifier = metadata_field.split(".")
    elif len(metadata_field.split(".")) == 2:
        schema, element = metadata_field.split(".")
        qualifier = None

    # First we need to get the schema ID
    sql = "SELECT metadata_schema_id FROM metadataschemaregistry WHERE short_id=%s;"
    # Syntax looks weird here, but the second argument must always be a sequence
    # See: https://www.psycopg.org/docs/usage.html
    cursor.execute(sql, [schema])

    if cursor.rowcount > 0:
        metadata_schema_id = cursor.fetchone()[0]

        # Now we can get the metadata field ID, paying attention to whether the
        # field has a qualifier or not.
        if qualifier:
            sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=%s AND element=%s AND qualifier=%s;"
            cursor.execute(sql, [metadata_schema_id, element, qualifier])
        else:
            sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=%s AND element=%s"
            cursor.execute(sql, [metadata_schema_id, element])

        if cursor.rowcount > 0:
            metadata_field_id = cursor.fetchone()[0]

    return metadata_field_id


def update_item_last_modified(cursor, dspace_object_id: str):
    """Update an item's last_modified timestamp.

    :param cursor: a psycopg cursor with an active database session.
    :param dspace_object_id: dspace_object_id of the item to update.
    """

    sql = "UPDATE item SET last_modified=NOW() WHERE uuid=%s;"
    # Syntax looks weird here, but the second argument must always be a sequence
    # See: https://www.psycopg.org/docs/usage.html
    cursor.execute(sql, [dspace_object_id])


def db_connect(
    database_name: str, database_user: str, database_pass: str, database_host: str
):
    """Connect to a PostgreSQL database.

    :param database_name: a string containing the database name.
    :param database_user: a string containing the database user.
    :param database_pass: a string containing the database pass.
    :param database_host: a string containing the database host.
    :returns psycopg connection
    """

    try:
        conn = psycopg.connect(
            f"dbname={database_name} user={database_user} password={database_pass} host={database_host}"
        )
    except psycopg.OperationalError:
        sys.stderr.write(Fore.RED + "Could not connect to database.\n" + Fore.RESET)
        sys.exit(1)

    return conn


def read_dois_from_file(input_file) -> list:
    """Read DOIs from a file.

    DOIs should be one per line with either http, https, dx.doi.org, doig.org
    or just the DOI itself. Anything other than the DOI will be stripped.

    :param input_file: a file handle (class _io.TextIOWrapper ???).
    :returns list of DOIs
    """

    # initialize an empty list for DOIs
    dois = []

    for line in input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # trim http://, https://, etc to make sure we only get the DOI component
        line = re.sub(r"^https?://(dx\.)?doi\.org/", "", line)

        # iterate over results and add DOIs that aren't already present
        if line not in dois:
            dois.append(line)

    # close input file before we exit
    input_file.close()

    return dois


def download_file(url, filename) -> bool:
    # Disable cache for streaming downloads
    # See: https://github.com/requests-cache/requests-cache/issues/75
    with requests_cache.disabled():
        r = requests.get(url, stream=True, allow_redirects=True)

    # Download failed for some reason
    if not r.ok:
        return False

    with open(filename, "wb") as f:
        # Make sure we handle zipped content. Note: this is not transport
        # compression, which is handled automatically by requests.
        try:
            content_encoding = r.headers["Content-Encoding"]
        except KeyError:
            content_encoding = None

        if content_encoding == "gzip":
            gzip_file = gzip.GzipFile(fileobj=r.raw)
            shutil.copyfileobj(gzip_file, f)
        else:
            shutil.copyfileobj(r.raw, f)

    # Check whether the file was written to disk after downloading
    if os.path.isfile(filename):
        return True
    else:
        return False
