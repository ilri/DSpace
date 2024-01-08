#!/usr/bin/env python3
#
# fix_maxmind_stats.py v0.0.1
#
# Fix DSpace statistics containing literal MaxMind city JSON objects, for
# example:
#
#   - com.maxmind.geoip2.record.City [ {"geoname_id":3936456,"names":{"de":"Lima","ru":"Лима","pt-BR":"Lima","ja":"リマ","en":"Lima","fr":"Lima","es":"Lima"}} ]
#   - com.maxmind.geoip2.record.City [ {} ]
#
# See: https://github.com/DSpace/DSpace/issues/9118
#
# The input file is a multi-line JSON exported from a DSpace 6.x Solr statistics
# core using solr-import-export-json. I exported all statistics documents that
# were affected using the Solr query "city:com*".
#
# Notes:
#
# I tried to use json from the stdlib but it doesn't support multi-line JSON.
# I tried to use pandas read_json(), but it introduces a whole bunch of other
# issues with data types, missing values, etc. In the end it was much simpler
# to use the jsonlines package.

import json
import os

import jsonlines


def fix_city(value):
    """Clean city string."""

    # Remove some crap so this can be a dict
    value = value.replace("com.maxmind.geoip2.record.City [ ", "")
    value = value.replace(" ]", "")

    # Try to read the cleaned string as a dict and access the English name
    try:
        # Assuming all city objects have an English version
        value = json.loads(value)["names"]["en"]
    except KeyError:
        value = ""

    return value


input_filename = "/home/aorth/Downloads/stats-maxmind-cities.json"
output_filename = "/home/aorth/Downloads/stats-maxmind-cities-fixed.json"

if os.path.exists(output_filename):
    os.remove(output_filename)

# Open the JSON file and iterate over each line as an object
with jsonlines.open(input_filename) as reader:
    for obj in reader:
        # Remove cities that are empty objects
        if obj["city"] == "com.maxmind.geoip2.record.City [ {} ]":
            del obj["city"]
        else:
            obj["city"] = fix_city(obj["city"])

        # Write each line back out (appending)
        with jsonlines.open(output_filename, mode="a") as writer:
            writer.write(obj)
