# util.py v0.0.2
#
# Copyright 2022 Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Various helper functions for CGSpace DSpace Python scripts.
#


def field_name_to_field_id(cursor, metadata_field: str):
    """Return the metadata_field_id for a given metadata field.

    TODO: handle case where schema doesn't exist
    TODO: handle case where metadata field doesn't exist

    :param cursor: a psycop2 cursor with an active database session.
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
        metadata_schema_id = cursor.fetchall()[0]

        # Now we can get the metadata field ID, paying attention to whether the
        # field has a qualifier or not.
        if qualifier:
            sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=%s AND element=%s AND qualifier=%s;"
            cursor.execute(sql, [metadata_schema_id, element, qualifier])
        else:
            sql = "SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=%s AND element=%s"
            cursor.execute(sql, [metadata_schema_id, element])

        if cursor.rowcount > 0:
            metadata_field_id = cursor.fetchall()[0]

    return metadata_field_id


def update_item_last_modified(cursor, dspace_object_id: str):
    """Update an item's last_modified timestamp.

    :param cursor: a psycop2 cursor with an active database session.
    :param dspace_object_id: dspace_object_id of the item to update.
    """

    sql = "UPDATE item SET last_modified=NOW() WHERE uuid=%s;"
    # Syntax looks weird here, but the second argument must always be a sequence
    # See: https://www.psycopg.org/docs/usage.html
    cursor.execute(sql, [dspace_object_id])
