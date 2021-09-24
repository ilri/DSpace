#!/usr/bin/env bash
#
# ./create-value-pairs.sh terms.txt terms-name

printf '<value-pairs value-pairs-name="%s">\n' $2

while read -r line
do
  printf '  <pair>\n'
  printf '    <displayed-value>%s</displayed-value>\n' "$line"
  printf '    <stored-value>%s</stored-value>\n' "$line"
  printf '  </pair>\n'
done < $1

printf '</value-pairs>'
