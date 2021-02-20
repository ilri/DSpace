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
240 247 #cg.creator.id→cg.creator.identifier
34  158 #dc.format.extent→dcterms.extent
15  170 #dc.date.issued→dcterms.issued
27  138 #dc.description.abstract→dcterms.abstract
26  156 #dc.description→dcterms.description
29  248 #dc.description.sponsorship→cg.contributor.donor
68  249 #dc.description.version→cg.reviewStatus
214 250 #cg.fulltextstatus→cg.howPublished
18  146 #dc.identifier.citation→dcterms.bibliographicCitation
206 139 #cg.identifier.status→dcterms.accessRights
38  172 #dc.language.iso→dcterms.language
113 180 #cg.link.reference→dcterms.relation
39  178 #dc.publisher→dcterms.publisher
43  166 #dc.relation.ispartofseries→dcterms.isPartOf
53  173 #dc.rights→dcterms.license
55  251 #dc.source→cg.journal
57  187 #dc.subject→dcterms.subject
109 191 #dc.type→dcterms.type
20  252 #dc.identifier.isbn→cg.isbn
21  253 #dc.identifier.issn→cg.issn
213  144 #cg.targetaudience→dcterms.audience
TO_MOVE

# psql stuff
readonly DATABASE_NAME=dspace63cgcorev2
readonly PSQL_BIN="/usr/bin/env psql"
# clean startup, and only print results
readonly PSQL_OPTS="--no-psqlrc --tuples-only -U postgres -h localhost --dbname $DATABASE_NAME"

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

        # call migrate_field() with format:
        # migrate_field 66 109
        migrate_field $row

        # relax!
        sleep 1
    done
}

main

# vim: set expandtab:ts=4:sw=4:bs=2
