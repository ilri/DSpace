# util.py v0.0.1
#
# Copyright 2022 Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Various helper functions for CGSpace DSpace Python scripts.
#


def update_item_last_modified(cursor, dspace_object_id: str):
    """Update an item's last_modified timestamp.

    :param cursor: a psycop2 cursor with an active database session.
    :param dspace_object_id: dspace_object_id of the item to update.
    """

    sql = "UPDATE item SET last_modified=NOW() WHERE uuid=%s;"
    # Syntax looks weird here, but the second argument must always be a sequence
    # See: https://www.psycopg.org/docs/usage.html
    cursor.execute(sql, [dspace_object_id])
