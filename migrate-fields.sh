#!/usr/bin/env bash
#
# Moves DSpace metadatavalues from one field to another. Assumed to be running
# as the `postgres` Linux user. You MUST perform a full Discovery reindex after
# doing this, ie: index-discovery -bf
#
# Alan Orth, April, 2016

# Exit on first error
set -o errexit

# IDs of fields to move, in this format:
#
# old_field new_field
#
# fields are separated with tabs or spaces. Uses bash's `mapfile` to read into
# an array.
mapfile -t fields_to_move <<TO_MOVE
72  55  #dc.source
86  230 #cg.contributor.crp
91  211 #cg.contributor.affiliation
94  212 #cg.species
107 231 #cg.coverage.subregion
126 3   #dc.contributor.author
73  219 #cg.identifier.url
74  220 #cg.identifier.doi
79  222 #cg.identifier.googleurl
89  223 #cg.identifier.dataurl
TO_MOVE

# psql stuff
readonly DATABASE_NAME=dspacetest
readonly PSQL_BIN="/usr/bin/env psql"
# clean startup, and only print results
readonly PSQL_OPTS="--no-psqlrc --tuples-only --dbname $DATABASE_NAME"

migrate_field() {
    local old_id=$1
    local new_id=$2
    # only modify item metadata (resource_type_id=2)
    local psql_cmd="UPDATE metadatavalue SET metadata_field_id=${new_id} WHERE metadata_field_id=${old_id} AND resource_type_id=2"

    $PSQL_BIN $PSQL_OPTS --echo-queries --command "$psql_cmd" \
        && return 0 \
        || return 1
}

main() {
    local row

    for row in "${fields_to_move[@]}"
    do
        # make sure row isn't a comment
        if [[ $row =~ ^[[:space:]]?# ]]; then
            continue
        fi

        # call migrate_field() with format:
        # migrate_field 66 109
        migrate_field $row

        # relax!
        sleep 1
    done
}

main

# vim: set expandtab:ts=4:sw=4:bs=2
