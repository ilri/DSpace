#!/usr/bin/env python3
#
# generate_solr_statistics.py v0.0.1
#
# Helper script to generate a bunch of Solr statistics based on a single
# reference statistic exported from a DSpace 6.3 Solr statistics core.
#
# The rationale for this was that we replaced a PDF bitstream and all
# downloads that had accumulated for the original PDF were deleted and
# the author wanted us to create the statistics again. According to the
# researcher, the item had ~3200 downloads from Mexico, Honduras, Brazil,
# Colombia, and Nicaragua before the PDF was deleted.

import json
import os
import random
from datetime import datetime
from uuid import uuid4

import jsonlines


def random_datetime() -> datetime:
    # When the item was uploaded to CGSpace
    start_date = datetime.fromisoformat("2023-09-26T00:00:00Z")
    # When the researcher last checked the statistics
    end_date = datetime.fromisoformat("2023-10-20T00:00:00Z")

    dt = random.random() * (end_date - start_date) + start_date

    return dt


def random_city(country_code: str) -> str:
    match country_code:
        case "MX":
            cities = [
                "Oaxaca",
                "Juarez",
                "Puebla",
                "Mexico",
                "Texmelucan",
                "Cancún",
                "Tultitlán",
                "Minatitlán",
            ]
        case "HN":
            cities = ["El Progreso", "Tegucigalpa", "San Pedro Sula", "La Ceiba"]
        case "CO":
            cities = [
                "Bogotá",
                "Medellín",
                "Cali",
                "Jamundi",
                "Barranquilla",
                "Villavicencio",
            ]
        case "BR":
            cities = [
                "Sao Luis",
                "Rio De Janeiro",
                "Guaira",
                "Cruzeiro Do Sul",
                "Santo Antonio De Jesus",
                "Valinhos",
                "Ituiutaba",
                "Sobradinho",
                "Maringa",
            ]
        case "NI":
            cities = [
                "Chinandega",
                "Managua",
                "Masaya",
                "San Juan Del Sur",
                "Matagalpa",
                "Estelí",
                "León",
                "Acoyapa",
            ]

    return random.choice(cities)


def country_continent(country_code: str) -> str:
    match country_code:
        case "MX":
            continent = "NA"
        case "HN":
            continent = "NA"
        case "CO":
            continent = "SA"
        case "BR":
            continent = "SA"
        case "NI":
            continent = "NA"

    return continent


# This is the reference statistic that we want to base our new
# statistics on.
# input_filename = "/home/aorth/Downloads/maria-no-atmire-schema.json"
input_filename = "/home/aorth/Downloads/maria.json"
output_filename = "/tmp/out.json"

if os.path.exists(output_filename):
    os.remove(output_filename)

with open(input_filename, "r") as f:
    json_data = json.load(f)

# Check if this statistic has fields from the Atmire CUA schema
if "cua_version" in json_data:
    atmire_cua = True
else:
    atmire_cua = False

# Delete some stuff that isn't required
del json_data["_version_"]  # Solr adds this automatically on insert
# Too annoying to do for fake statistics, and not needed by any usage graphs
del json_data["ip"]
del json_data["dns"]
del json_data["latitude"]
del json_data["longitude"]

# Don't think we need these. The *_ngram and *_search fields are custom Atmire
# modifications to the Solr schema that get copied from the relevant field on
# insert.
if atmire_cua:
    del json_data["ip_ngram"]
    del json_data["ip_search"]
    del json_data["referrer_ngram"]
    del json_data["referrer_search"]
    del json_data["userAgent_ngram"]
    del json_data["userAgent_search"]
    del json_data["countryCode_ngram"]
    del json_data["countryCode_search"]

# Set a user agent. Hey it's me!
json_data[
    "userAgent"
] = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"

# Open the output file. This is ghetto because we write each line individually
# in each loop iteration below.
with jsonlines.open(output_filename, mode="a") as writer:
    for country_code in ["MX", "HN", "CO", "BR", "NI"]:
        json_data["countryCode"] = country_code
        if atmire_cua:
            json_data["geoIpCountryCode"] = [country_code]
        json_data["continent"] = country_continent(country_code)

        for x in range(640):
            dt = random_datetime()
            # Set a random time in our range
            json_data["time"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            if atmire_cua:
                json_data["dateYear"] = dt.strftime("%Y")
                json_data["dateYearMonth"] = dt.strftime("%Y-%m")

            # Set a random city from our list
            json_data["city"] = random_city(country_code)
            # Set a unique UUIDv4 (required in Solr stats schema)
            json_data["uid"] = str(uuid4())

            writer.write(json_data)
