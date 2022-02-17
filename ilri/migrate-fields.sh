#!/usr/bin/env bash
#
# Moves DSpace metadatavalues from one field to another. Assumed to be running
# as the `postgres` Linux user. You MUST perform a full Discovery reindex after
# doing this, ie: index-discovery -bf
#
# Alan Orth, April, 2016

# Exit on first error
set -o errexit

# Names of fields to move, in this format:
#
# old_field new_field
#
# fields are separated with tabs or spaces. Uses bash's `mapfile` to read into
# an array.
mapfile -t fields_to_move <<TO_MOVE
dc.format.extent            dcterms.extent
dc.date.issued              dcterms.issued
dc.description.abstract     dcterms.abstract
dc.description              dcterms.description
dc.description.sponsorship  cg.contributor.donor
dc.description.version      cg.reviewStatus
dc.identifier.citation      dcterms.bibliographicCitation
dc.language.iso             dcterms.language
dc.publisher                dcterms.publisher
dc.relation.ispartofseries  dcterms.isPartOf
dc.rights                   dcterms.license
dc.source                   cg.journal
dc.subject                  dcterms.subject
dc.type                     dcterms.type
dc.identifier.isbn          cg.isbn
dc.identifier.issn          cg.issn
TO_MOVE

# psql stuff
readonly DATABASE_NAME=dspacetest
readonly PSQL_BIN="/usr/bin/env psql"
# clean startup, and only print results without whitespace
readonly PSQL_OPTS="--no-psqlrc --tuples-only -A -U postgres -h localhost --dbname $DATABASE_NAME"

lookup_field_id() {
    local field=$1
    local schema=$(echo $field | cut -d. -f1)
    local element=$(echo $field | cut -d. -f2)
    local qualifier=$(echo $field | cut -d. -f3)

    # Check if schema (ie "dc") is set and get its ID
    if [[ $schema ]]; then
        local psql_cmd="SELECT metadata_schema_id FROM metadataschemaregistry WHERE short_id='${schema}'"
        local schema_id=$($PSQL_BIN $PSQL_OPTS --command "$psql_cmd")
    fi

    # Check if field has an element qualifier, ie dc.description.abstract
    if [[ $qualifier ]]; then
        psql_cmd="SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=${schema_id} AND element='${element}' AND qualifier='${qualifier}'"
        local field_id=$($PSQL_BIN $PSQL_OPTS --command "$psql_cmd")
    else
        # If there is no qualifier then we need to use "IS NULL"
        psql_cmd="SELECT metadata_field_id FROM metadatafieldregistry WHERE metadata_schema_id=${schema_id} AND element='${element}' AND qualifier IS NULL"
        local field_id=$($PSQL_BIN $PSQL_OPTS --command "$psql_cmd")
    fi

    echo $field_id
}

migrate_field() {
    local old_id=$1
    local new_id=$2
    # only modify item metadata (make sure item's UUID is in the item table)
    local psql_cmd="UPDATE metadatavalue SET metadata_field_id=${new_id} WHERE metadata_field_id=${old_id} AND dspace_object_id IN (SELECT uuid FROM item)"

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

        field_from=$(echo $row | awk '{print $1}')
        field_to=$(echo $row | awk '{print $2}')

        field_from_id=$(lookup_field_id $field_from)
        if [[ ! $field_from_id ]]; then
            echo "Make sure $field_from exists in the DSpace metadata registry."

            exit 1
        fi

        field_to_id=$(lookup_field_id $field_to)
        if [[ ! $field_to_id ]]; then
            echo "Make sure $field_to exists in the DSpace metadata registry."

            exit 1
        fi

        echo "Migrating $field_from → $field_to"
        migrate_field $field_from_id $field_to_id
    done
}

main

# vim: set expandtab:ts=4:sw=4:bs=2
