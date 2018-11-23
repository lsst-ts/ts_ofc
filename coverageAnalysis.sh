#!/bin/bash

# Get the files
FILES=$1

# Do the coverage analysis for each file
for FILE in $(/bin/ls $FILES)
do
	coverage run -p $FILE
done

coverage combine
coverage report --omit=".local/*"

# Generate the html report
# Ignore the coverage of test scripts
coverage html --omit=".local/*","test*.py"
