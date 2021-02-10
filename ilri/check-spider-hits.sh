#!/usr/bin/env bash
#
# check-spider-hits.sh v1.2.0
#
# Copyright (C) 2019-2020 Alan Orth
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
readonly DEF_SPIDERS_PATTERN_FILE=/dspace/config/spiders/agents/example
readonly DEF_SOLR_URL=http://localhost:8081/solr
readonly DEF_STATISTICS_SHARD=statistics

######

readonly PROGNAME=$(basename $0)
readonly ARGS="$@"

function usage() {
    cat <<-EOF
Usage: $PROGNAME [-d] [-f $DEF_SPIDERS_PATTERN_FILE] [-p] [-s $DEF_STATISTICS_SHARD] [-u $DEF_SOLR_URL]

Optional arguments:
    -d: print debug messages
    -f: path to file containing spider user agent patterns¹ (default: $DEF_SPIDERS_PATTERN_FILE)
    -p: purge statistics that match spider user agents
    -s: Solr statistics shard, for example statistics or statistics-2018² (default: $DEF_STATISTICS_SHARD)
    -u: URL to Solr (default: $DEF_SOLR_URL)

Written by: Alan Orth <a.orth@cgiar.org>

¹ DSpace ships an "example" pattern file that works well. Another option is the patterns file maintained by the COUNTER-Robots project.
² If your statistics core has been split into yearly "shards" by DSpace's stats-util you need to search each shard separately.
EOF

    exit 0
}

function parse_options() {
    while getopts ":df:ps:u:" opt; do
        case $opt in
            d)
                DEBUG=yes
                ;;
            f)
                SPIDERS_PATTERN_FILE=$OPTARG

                if ! [[ -r "$SPIDERS_PATTERN_FILE" ]]; then
                    echo "(ERROR) Spider patterns file \"$SPIDERS_PATTERN_FILE\" doesn't exist."

                    exit 1
                fi
                ;;
            p)
                PURGE_SPIDER_HITS=yes
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

[[ $DEBUG ]] && echo "(DEBUG) Using spiders pattern file: $SPIDERS_PATTERN_FILE"


# Make a temporary copy of the spider file so we can do pattern replacement
# inside it with sed rather than using stdout from sed and having to deal
# with spaces and newlines in bash.
SPIDERS_PATTERN_FILE_TEMP=$(mktemp)
cp "$SPIDERS_PATTERN_FILE" "$SPIDERS_PATTERN_FILE_TEMP"

# Read list of spider user agents from the patterns file, converting PCRE-style
# regular expressions to a format that is easier to deal with in bash (spaces!)
# and that Solr supports (ie, patterns are anchored by ^ and $ implicitly, and
# some character types like \d are not supported).
#
# See: https://1opensourcelover.wordpress.com/2013/09/29/solr-regex-tutorial/
#
# For now this seems to be enough:
#   - Replace \s with a literal space
#   - Replace \d with [0-9] character class
#   - Unescape dashes
#   - Escape @
#
sed -i -e 's/\\s/ /g' -e 's/\\d/[0-9]/g' -e 's/\\-/-/g' -e 's/@/\\@/g' $SPIDERS_PATTERN_FILE_TEMP

# Start a tally of bot hits so we can report the total at the end
BOT_HITS=0

while read -r spider; do
    # Save the original pattern so we can inform the user later
    original_spider=$spider

    # Skip patterns that contain a plus or percent sign (+ or %) because they
    # are tricky to deal with in Solr. For some reason escaping them seems to
    # work for searches, but not for deletes. I don't have time to figure it
    # out.
    if [[ $spider =~ [%\+] ]]; then
        [[ $DEBUG ]] && echo "(DEBUG) Skipping spider: $original_spider"
        continue
    fi


    unset has_beginning_anchor
    unset has_end_anchor

    # Remove ^ at the beginning because it is implied in Solr's regex search
    if [[ $spider =~ ^\^ ]]; then
        spider=$(echo $spider | sed -e 's/^\^//')

        # Record that this spider's original user agent pattern had a ^
        has_beginning_anchor=yes
    fi

    # Remove $ at the end because it is implied in Solr's regex search
    if [[ $spider =~ \$ ]]; then
        spider=$(echo $spider | sed -e 's/\$$//')

        # Record that this spider's original user agent pattern had a $
        has_end_anchor=yes
    fi

    # If the original pattern did NOT have a beginning anchor (^), then add a
    # wildcard at the beginning.
    if [[ -z $has_beginning_anchor ]]; then
        spider=".*$spider"
    fi

    # If the original pattern did NOT have an ending enchor ($), then add a
    # wildcard at the end.
    if [[ -z $has_end_anchor ]]; then
        spider="$spider.*"
    fi

    [[ $DEBUG ]] && echo "(DEBUG) Checking for hits from spider: $original_spider"

    # Check for hits from this spider in Solr and save results into a variable,
    # setting a custom curl output format so I can get the HTTP status code and
    # Solr response in one request, then tease them out later.
    solr_result=$(curl -s -w "http_code=%{http_code}" "$SOLR_URL/$STATISTICS_SHARD/select" -d "q=userAgent:/$spider/&rows=0")

    http_code=$(echo $solr_result | grep -o -E 'http_code=[0-9]+' | awk -F= '{print $2}')

    # Check the Solr HTTP response code and skip spider if not successful
    if [[ $http_code -ne 200 ]]; then
        [[ $DEBUG ]] && echo "(DEBUG) Solr query returned HTTP $http_code, skipping $original_spider."

        continue
    fi

    # lazy extraction of Solr numFound (relies on sed -E for extended regex)
    numFound=$(echo $solr_result | sed -E 's/\s+http_code=[0-9]+//' | xmllint --format - | grep numFound | sed -E 's/^.*numFound="([0-9]+)".*$/\1/')

    if [[ numFound -gt 0 ]]; then
        if [[ $PURGE_SPIDER_HITS ]]; then
            echo "Purging $numFound hits from $original_spider in $STATISTICS_SHARD"

            # Purge the hits and soft commit
            curl -s "$SOLR_URL/$STATISTICS_SHARD/update?softCommit=true" -H "Content-Type: text/xml" --data-binary "<delete><query>userAgent:/$spider/</query></delete>" > /dev/null 2>&1
        else
            echo "Found $numFound hits from $original_spider in $STATISTICS_SHARD"
        fi

        BOT_HITS=$((BOT_HITS+numFound))
    fi
done < "$SPIDERS_PATTERN_FILE_TEMP"

if [[ $BOT_HITS -gt 0 ]]; then
    if [[ $PURGE_SPIDER_HITS ]]; then
        echo
        echo "Total number of bot hits purged: $BOT_HITS"

        # Hard commit after we're done processing all spiders
        curl -s "$SOLR_URL/$STATISTICS_SHARD/update?commit=true" > /dev/null 2>&1
    else
        echo
        echo "Total number of hits from bots: $BOT_HITS"
    fi
fi

if [[ -f "$SPIDERS_PATTERN_FILE_TEMP" ]]; then
    rm "$SPIDERS_PATTERN_FILE_TEMP"
fi

# vim: set expandtab:ts=4:sw=4:bs=2
