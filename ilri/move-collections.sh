#!/usr/bin/env bash
#
# Moves DSpace collections from one community to another. Takes a list of
# handles, then resolves their internal resource_id's and reassigns the
# community relationship. Assumed to be running as `postgres` Linux user.
#
# I don't think reindexing is required, because no metadata has changed,
# and therefore no search or browse indexes need to be updated.
#
# Alan Orth, January, 2016

# Exit on first error
set -o errexit

# Read handles to move into an array
# format:
#
# collection from_community to_community
#
# Handles are separated with tabs or spaces. Uses `mapfile` to read into
# an array.
mapfile -t items_to_move <<TO_MOVE
10568/51821 10568/42212 10568/42211
10568/51400 10568/42214 10568/42211
10568/56992 10568/42216 10568/42211
10568/42218 10568/42217 10568/42211
TO_MOVE

# psql stuff
readonly DATABASE_NAME=dspacetest
readonly PSQL_BIN='/usr/bin/env psql'
# clean startup, and only print results
readonly PSQL_OPTS="--no-psqlrc --tuples-only --dbname $DATABASE_NAME"

# Get an internal resource id for a handle (community / collection)
get_resource_id() {
    local handle=$1
    local psql_cmd="SELECT resource_id FROM handle WHERE handle = '$handle'"

    $PSQL_BIN $PSQL_OPTS --command "$psql_cmd" | sed -e '/^$/d' -e 's/^[ \t]*//' \
        && return 0 \
        || return 1
}

move_collection() {
    local collection_id=$(get_resource_id $1)
    local old_community_id=$(get_resource_id $2)
    local new_community_id=$(get_resource_id $3)
    local psql_cmd="UPDATE community2collection SET community_id='$new_community_id' WHERE community_id='$old_community_id' and collection_id='$collection_id'"

    if [[ -z $collection_id || -z $old_community_id || -z $new_community_id ]]; then
        echo "Problem moving collection $1. Please make sure the to and from communities are correct."
        return 1
    fi

    $PSQL_BIN $PSQL_OPTS --echo-queries --command "$psql_cmd" \
        && return 0 \
        || return 1
}

main() {
    local row

    for row in "${items_to_move[@]}"
    do
        # make sure row isn't a comment
        if [[ $row =~ ^[[:space:]]?# ]]; then
            continue
        fi

        # call move_collection with format:
        # move_collection 10658/123 10568/456 10568/789
        move_collection $row
    done
}

main

# vim: set expandtab:ts=4:sw=4:bs=2
