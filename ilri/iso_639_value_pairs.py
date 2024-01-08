#!/usr/bin/env python3
#
# Ghetto script to export value pairs for ISO 639-1 Alpha 2 codes from pycountry

import pycountry

for language in pycountry.languages:
    try:
        language.alpha_2
    except:
        continue

    print("     <pair>")
    print(f"       <displayed-value>{language.name}</displayed-value>")
    print(f"       <stored-value>{language.alpha_2}</stored-value>")
    print("     </pair>")

print("     <pair>")
print("       <displayed-value>N/A</displayed-value>")
print("       <stored-value></stored-value>")
print("     </pair>")
print("     <pair>")
print("       <displayed-value>(Other)</displayed-value>")
print("       <stored-value>other</stored-value>")
print("     </pair>")
