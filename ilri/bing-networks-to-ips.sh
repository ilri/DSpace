#!/usr/bin/env bash
#
# Latest as of 2022-07-06. For printing the IPs in each CIDR network so that I
# can purge them all from Solr statistics using check-spider-ip-hits.sh.

BINGBOT_JSON_URL=https://www.bing.com/toolbox/bingbot.json
# Extract the networks from the JSON (I wrote this using https://jqplay.org/)
BINGBOT_NETWORKS=$(http "$BINGBOT_JSON_URL" \
                    | jq --raw-output '.["prefixes"][].ipv4Prefix')

for network in $BINGBOT_NETWORKS; do
    # Use prips to print IPs in given CIDR and strip network and broadcast.
    # See: https://stackoverflow.com/a/52501093/1996540
    prips "$network" | sed -e '1d; $d'
done
