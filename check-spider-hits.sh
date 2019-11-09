#!/usr/bin/env bash
#
# check-spider-hits.sh v1.0.0
#
# Copyright (C) 2019 Alan Orth
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

# Exit on first error
set -o errexit

# defaults
readonly DEF_PURGE_SPIDER_HITS=no
readonly DEF_SPIDERS_PATTERN_FILE=~/src/git/DSpace/dspace/config/spiders/agents/example
readonly DEF_SOLR_URL=http://localhost:8081/solr
readonly DEF_STATISTICS_SHARD=statistics

######

readonly PROGNAME=$(basename $0)
readonly ARGS="$@"

function usage() {
    cat <<-EOF
Usage: $PROGNAME [-f] [-m] [-s] [-u]

Optional arguments:
    -f: path to file containing spider user agent patterns (default: $DEF_SPIDERS_PATTERN_FILE)
    -p: purge statistics that match spider user agents (yes or no, default: $DEF_PURGE_SPIDER_HITS)
    -s: Solr statistics shard, for example statistics or statistics-2018 (default: $DEF_STATISTICS_SHARD)
    -u: URL to Solr (default: $DEF_SOLR_URL)

Written by: Alan Orth <a.orth@cgiar.org>
EOF

    exit 0
}

function parse_options() {
    while getopts ":f:p:s:u:" opt; do
        case $opt in
            f)
                SPIDERS_PATTERN_FILE=$OPTARG
                ;;
            p)
                # make sure -p is passed yes or no
                if ! [[ "$OPTARG" =~ ^(yes|no)$ ]]; then
                    usage
                fi

                PURGE_SPIDER_HITS=$OPTARG
                ;;
            s)
                STATISTICS_SHARD=$OPTARG
                ;;
            u)
                # make sure -s is passed something like a URL
                if ! [[ "$OPTARG" =~ ^https?://.*$ ]]; then
                    usage
                fi

                SOLR_URL=$OPTARG
                ;;
            \?|:)
                usage
                ;;
        esac
    done
}

function envsetup() {
    # check to see if user specified a Solr URL
    # ... otherwise use the default
    if [[ -z $SOLR_URL ]]; then
        SOLR_URL=$DEF_SOLR_URL
    fi

    # check to see if user wants to purge spider hits
    # ... otherwise use the default
    if [[ -z $PURGE_SPIDER_HITS ]]; then
        PURGE_SPIDER_HITS=$DEF_PURGE_SPIDER_HITS
    fi

    # check to see if user specified a spiders pattern file
    # ... otherwise use the default
    if [[ -z $SPIDERS_PATTERN_FILE ]]; then
        SPIDERS_PATTERN_FILE=$DEF_SPIDERS_PATTERN_FILE
    fi

    # check to see if user specified Solr statistics shards
    # ... otherwise use the default
    if [[ -z $STATISTICS_SHARD ]]; then
        STATISTICS_SHARD=$DEF_STATISTICS_SHARD
    fi
}

# pass the shell's argument array to the parsing function
parse_options $ARGS

# set up the defaults
envsetup

# Read list of spider user agents from the patterns file. For now, only read
# patterns that don't have regular expression or space characters, because we
# they are tricky to parse in bash and Solr's regular expression search uses
# a different format (patterns are anchored with ^ and $ by default and some
# meta characters like \d are not supported).
SPIDERS=$(grep -v -E '(\^|\\|\[|\]|!|\?|\.|\s)' $SPIDERS_PATTERN_FILE)

# Start a tally of bot hits so we can report the total at the end
BOT_HITS=0

for spider in $SPIDERS; do
    # lazy extraction of Solr numFound (relies on sed -E for extended regex)
    numFound=$(curl -s "$SOLR_URL/$STATISTICS_SHARD/select?q=userAgent:*$spider*&rows=0" | xmllint --format - | grep numFound | sed -E 's/^.*numFound="([0-9]+)".*$/\1/')

    if [[ numFound -gt 0 ]]; then
        if [[ $PURGE_SPIDER_HITS == 'yes' ]]; then
            echo "Purging $numFound hits from $spider in $STATISTICS_SHARD"

            # Purge the hits and soft commit
            curl -s "$SOLR_URL/$STATISTICS_SHARD/update?softCommit=true" -H "Content-Type: text/xml" --data-binary "<delete><query>userAgent:*$spider*</query></delete>" > /dev/null 2>&1
        else
            echo "Found $numFound hits from $spider in $STATISTICS_SHARD"
        fi

        BOT_HITS=$((BOT_HITS+numFound))
    fi
done

if [[ $BOT_HITS -gt 0 ]]; then
    if [[ $PURGE_SPIDER_HITS == 'yes' ]]; then
        echo
        echo "Total number of bot hits purged: $BOT_HITS"

        # Hard commit after we're done processing all spiders
        curl -s "$SOLR_URL/$STATISTICS_SHARD/update?commit=true" > /dev/null 2>&1
    else
        echo
        echo "Total number of hits from bots: $BOT_HITS"
    fi
fi

# vim: set expandtab:ts=4:sw=4:bs=2
