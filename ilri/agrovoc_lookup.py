#!/usr/bin/env python3
#
# agrovoc-lookup.py 0.4.2
#
# Copyright Alan Orth.
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# Queries the public AGROVOC REST API for subjects read from a text file. Text
# file should have one subject per line. Results are saved to a CSV including
# the subject, the language, the match type, and the total number of matches.
#
# This script is written for Python 3.6+ and requires several modules that you
# can install with pip (I recommend using a Python virtual environment):
#
#   $ pip install colorama requests requests-cache
#

import argparse
import csv
import signal
import sys
from datetime import timedelta

import requests
import requests_cache
from colorama import Fore


# read subjects from a text file, one per line
def read_subjects_from_file():
    # initialize an empty list for subjects
    subjects = []

    for line in args.input_file:
        # trim any leading or trailing whitespace (including newlines)
        line = line.strip()

        # iterate over results and add subjects that aren't already present
        if line not in subjects:
            subjects.append(line)

    # close input file before we exit
    args.input_file.close()

    resolve_subjects(subjects)


def resolve_subjects(subjects):
    fieldnames = ["subject", "language", "match type", "number of matches"]
    writer = csv.DictWriter(args.output_file, fieldnames=fieldnames)
    writer.writeheader()

    # enable transparent request cache with thirty days expiry, as AGROVOC only
    # makes new releases monthly so this should be safe.
    expire_after = timedelta(days=30)
    requests_cache.install_cache("requests-cache", expire_after=expire_after)

    # prune old cache entries
    requests_cache.delete()

    for subject in subjects:
        if args.debug:
            sys.stderr.write(
                Fore.GREEN
                + f"Looking up the subject: {subject} ({'any' or args.language})\n"
                + Fore.RESET
            )

        request_url = "https://agrovoc.uniroma2.it/agrovoc/rest/v1/agrovoc/search"
        request_params = {"query": subject}

        if args.language:
            # use user specified language
            request_params.update(lang=args.language)

        request = requests.get(request_url, params=request_params)

        if request.status_code == requests.codes.ok:
            data = request.json()

            # Assume no match
            matched = False

            number_of_matches = len(data["results"])

            # no results means no match
            if number_of_matches == 0:
                if args.debug:
                    sys.stderr.write(
                        Fore.YELLOW
                        + f"No match for {subject!r} in AGROVOC (cached: {request.from_cache})\n"
                        + Fore.RESET
                    )

                writer.writerow(
                    {
                        "subject": subject,
                        "language": "",
                        "match type": "",
                        "number of matches": number_of_matches,
                    }
                )
            elif number_of_matches >= 1:
                for result in request.json()["results"]:
                    # if there is more than one result we need to check each for
                    # a preferred or matchedPreLabel match first. If there are
                    # none then we can check each result again for an altLabel
                    # matches.alternate match. Note that we need to make sure
                    # they actually exist before attempting to reference them.
                    # If they don't exist then we'll catch the exception and set
                    # the values to None.
                    #
                    # Note that matchedPrefLabel is not a property in the SKOS/
                    # SKOSXL vocabulary. It seems to be a hint returned by the
                    # SKOSMOS server to indicate that the search term matched
                    # the prefLabel of some language.
                    try:
                        result["prefLabel"]
                    except KeyError:
                        result["prefLabel"] = None

                    try:
                        result["matchedPrefLabel"]
                    except KeyError:
                        result["matchedPrefLabel"] = None

                    # upper case our subject and the AGROVOC result to make sure
                    # we're comparing the same thing because AGROVOC returns the
                    # title case like "Iran" no matter whether you search for
                    # "IRAN" or "iran".
                    if (
                        result["prefLabel"]
                        and subject.upper() == result["prefLabel"].upper()
                    ):
                        matched = True
                        language = result["lang"]
                        print(
                            f"Match for {subject!r} in AGROVOC {language} (cached: {request.from_cache})"
                        )

                        writer.writerow(
                            {
                                "subject": subject,
                                "language": language,
                                "match type": "prefLabel",
                                "number of matches": number_of_matches,
                            }
                        )

                        break
                    elif (
                        result["matchedPrefLabel"]
                        and subject.upper() == result["matchedPrefLabel"].upper()
                    ):
                        matched = True
                        language = result["lang"]
                        print(
                            f"Match for {subject!r} in AGROVOC {language} (cached: {request.from_cache})"
                        )

                        writer.writerow(
                            {
                                "subject": subject,
                                "language": language,
                                "match type": "prefLabel",
                                "number of matches": number_of_matches,
                            }
                        )

                        break

                # If we're here we assume there were no matches for prefLabel or
                # matchedPrefLabel in the results, so now we will check for an
                # altLabel match.
                if not matched:
                    for result in request.json()["results"]:
                        # make sure key exists before trying to access it
                        try:
                            result["altLabel"]
                        except KeyError:
                            result["altLabel"] = None

                        if (
                            result["altLabel"]
                            and subject.upper() == result["altLabel"].upper()
                        ):
                            matched = True
                            language = result["lang"]
                            print(
                                f"Match for {subject!r} in AGROVOC {language} (cached: {request.from_cache})"
                            )

                            writer.writerow(
                                {
                                    "subject": subject,
                                    "language": language,
                                    "match type": "altLabel",
                                    "number of matches": number_of_matches,
                                }
                            )

                            break

    # close output files before we exit
    args.output_file.close()


def signal_handler(signal, frame):
    # close output files before we exit
    args.output_file.close()

    sys.exit(1)


parser = argparse.ArgumentParser(
    description="Query the AGROVOC REST API to validate subject terms from a text file and save results in a CSV."
)
parser.add_argument(
    "-d",
    "--debug",
    help="Print debug messages to standard error (stderr).",
    action="store_true",
)
parser.add_argument(
    "-i",
    "--input-file",
    help="File name containing subject terms to look up.",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-l", "--language", help="Language to query terms (example en, default any)."
)
parser.add_argument(
    "-o",
    "--output-file",
    help="Name of output file to write results to (CSV).",
    required=True,
    type=argparse.FileType("w", encoding="UTF-8"),
)
args = parser.parse_args()

# set the signal handler for SIGINT (^C) so we can exit cleanly
signal.signal(signal.SIGINT, signal_handler)

# if the user specified an input file, get the addresses from there
if args.input_file:
    read_subjects_from_file()

exit()
