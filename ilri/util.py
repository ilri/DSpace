# util.py v0.0.7
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
from datetime import timedelta

import psycopg
from colorama import Fore
from requests_cache import CachedSession

session = CachedSession(
    "requests-cache", expire_after=timedelta(days=30), allowable_codes=(200, 404)
)
# prune old cache entries
session.cache.delete(expired=True)


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

    DOIs should be one per line with either http, https, dx.doi.org, doi.org
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
    with session.cache_disabled():
        r = session.get(url, stream=True, allow_redirects=True)

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


def normalize_doi(doi):
    """
    Try to normalize a DOI based on some cases I noticed. Return a clean
    DOI in https://doi.org/10. format, lowercased, and stripped.
    """

    if not doi:
        return ""

    # normalize DOIs like doi:10.1088/1748-9326/ac413a
    doi = doi.replace("doi:", "")

    # fix typo in DOIs like 0.1002/2014WR016668
    if doi.startswith("0."):
        doi = f"1{doi}"

    # fix typo in DOIs like http://dx.doi.org/DOI:
    doi = doi.replace("http://dx.doi.org/DOI:", "")

    # fix old dx.doi.org
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)

    # fix typo in DOI URI like https:// doi.org/10.3390/agronomy13030727
    doi = doi.replace("https:// doi.org/", "")

    # fix URLs that should be DOIs like https://www.tandfonline.com/doi/full/10.1080/23322039.2019.1640098
    doi = doi.replace("https://www.tandfonline.com/doi/full/", "")

    # fix Unicode non-printing characters like in 10.​1007/​s10113-016-0983-6
    pattern = re.compile(r"\u200B")
    match = re.findall(pattern, doi)

    if match:
        doi = re.sub(pattern, "", doi)

    # return the normalized DOI, and strip it just in case
    return f"https://doi.org/{doi.lower().strip()}"


def normalize_cgiar_affiliations(affiliations):
    """
    Try to normalize affiliations. For now this is a manual list of replacements
    for CGIAR centers only.
    """
    if not affiliations:
        return []

    affiliations_normalized = list()

    for affiliation in affiliations:
        # Strip some nonsense at the beginning and end
        affiliation = affiliation.strip(";.[§¶*†")

        # Strip some acronymns at the end
        affiliation = re.sub(r"\s+\(\w+\)$", "", affiliation)

        affiliation = re.sub(
            r"^Africa Rice Center.+", "Africa Rice Center", affiliation
        )
        affiliation = re.sub(r"^AfricaRice.*", "Africa Rice Center", affiliation)

        affiliation = re.sub(
            r"^Alliance of Bioversity International and.*",
            "Alliance of Bioversity International and CIAT",
            affiliation,
        )

        affiliation = re.sub(
            r"^Bioversity International.*", "Bioversity International", affiliation
        )

        affiliation = re.sub(
            r"^Cent(er|re) for International Forestry Research.*",
            "Center for International Forestry Research",
            affiliation,
        )
        affiliation = re.sub(
            r"^CIFOR.*", "Center for International Forestry Research", affiliation
        )

        affiliation = re.sub(
            r"^International Cent(er|re) for Agricultural Research in the Dry Areas.*",
            "International Center for Agricultural Research in the Dry Areas",
            affiliation,
        )
        affiliation = re.sub(
            r"^ICARDA.*",
            "International Center for Agricultural Research in the Dry Areas",
            affiliation,
        )

        affiliation = re.sub(
            r"^International Cent(er|re) for Tropical Agriculture.*",
            "International Center for Tropical Agriculture",
            affiliation,
        )
        affiliation = re.sub(
            r"^Centro Internacional de Agricultura Tropical.*",
            "International Center for Tropical Agriculture",
            affiliation,
        )
        affiliation = re.sub(
            r"^CIAT.*", "International Center for Tropical Agriculture", affiliation
        )

        affiliation = re.sub(
            r"^International Crops Research Institute for the Semi-Arid Tropics.*",
            "International Crops Research Institute for the Semi-Arid Tropics",
            affiliation,
        )
        affiliation = re.sub(
            r"^ICRISAT.*",
            "International Crops Research Institute for the Semi-Arid Tropics",
            affiliation,
        )

        affiliation = re.sub(
            r"^International Food Policy Research Institute.*",
            "International Food Policy Research Institute",
            affiliation,
        )
        affiliation = re.sub(
            r"^IFPRI.*", "International Food Policy Research Institute", affiliation
        )

        affiliation = re.sub(
            r"^International Institute of Tropical Agriculture.*",
            "International Institute of Tropical Agriculture",
            affiliation,
        )
        affiliation = re.sub(
            r"^IITA.*", "International Institute of Tropical Agriculture", affiliation
        )

        affiliation = re.sub(
            r"^International Livestock Research Institute.*",
            "International Livestock Research Institute",
            affiliation,
        )
        affiliation = re.sub(
            r"^International Livestock Research Centre.*",
            "International Livestock Research Institute",
            affiliation,
        )
        affiliation = re.sub(
            r"^ILRI.*", "International Livestock Research Institute", affiliation
        )

        affiliation = re.sub(
            r"^International Maize and Wheat Improvement Cent(er|re).*",
            "International Maize and Wheat Improvement Center",
            affiliation,
        )
        affiliation = re.sub(
            r"^Centro Internacional de Mejoramiento de Ma(i|í)z y Trigo.*",
            "International Maize and Wheat Improvement Center",
            affiliation,
        )
        affiliation = re.sub(
            r"^CIMMYT.*",
            "International Maize and Wheat Improvement Center",
            affiliation,
        )

        affiliation = re.sub(
            r"^International Potato Cent(er|re).*",
            "International Potato Center",
            affiliation,
        )
        affiliation = re.sub(
            r"^Centro Internacional de la Papa.*",
            "International Potato Center",
            affiliation,
        )
        affiliation = re.sub(r"^CIP.*", "International Potato Center", affiliation)

        affiliation = re.sub(
            r"^International Rice Research Institute.*",
            "International Rice Research Institute",
            affiliation,
        )
        affiliation = re.sub(
            r"^IRRI.*", "International Rice Research Institute", affiliation
        )

        affiliation = re.sub(
            r"^International Water Management Institute.*",
            "International Water Management Institute",
            affiliation,
        )
        affiliation = re.sub(
            r"^IWMI.*", "International Water Management Institute", affiliation
        )

        affiliation = re.sub(
            r"^World Agroforestry Cent(er|re)\s?.*", "World Agroforestry", affiliation
        )
        affiliation = re.sub(
            r"^International Cent(er|re) for Research in Agroforestry.*",
            "World Agroforestry",
            affiliation,
        )
        affiliation = re.sub(r"^ICRAF.*", "World Agroforestry", affiliation)

        affiliation = re.sub(r"^WorldFish.*", "WorldFish", affiliation)

        if affiliation not in affiliations_normalized:
            affiliations_normalized.append(affiliation)

    return affiliations_normalized
