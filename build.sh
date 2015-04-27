#!/bin/bash
#Add commit!

# rudimentary strip of .properties from end of 1st argument
# mostly because I ./build.sh blah<tab> to complete the site
# I'm building for, and maven expects the argument for the
# properties file to not have it.
BUILD_PROP_FILE=$1
readonly BUILD_PROP_REGEX="^.*\.properties$"

if [[ $BUILD_PROP_FILE =~ $BUILD_PROP_REGEX ]]; then
    BUILD_PROP_FILE=${BUILD_PROP_FILE%.properties}
fi

mvn -U -Pxpdf-mediafilter-support -Denv=$BUILD_PROP_FILE clean package

exit 1
