#!/usr/bin/env bash
# set -euo pipefail             # safer bash

outFile="instance-md5sum.csv"
echo "instance,hashValue" >"$outFile"

shopt -s nullglob             # let globs expand to an empty array instead of a literal

# Look for .dzn
files=(inst-*.dzn)

# If no .dzn, go to default
if [ ${#files[@]} -eq 0 ]; then
    files=(inst-*.param)   # Default patter
fi

# Exit if still none found
if [ ${#files[@]} -eq 0 ]; then
    echo "No instance files found (neither .dzn nor .param)."
    exit 1
fi

# Hash each file
for fn in "${files[@]}"; do
    if [[ "$(uname)" == "Darwin" ]]; then
        val=$(md5 "$fn"   | cut -d"=" -f2 | xargs)
    elif [[ "$(expr substr $(uname -s) 1 5)" == "Linux" ]]; then
        val=$(md5sum "$fn" | cut -d' ' -f1)
    else
        echo "Sorry, we only support Linux and macOS at the moment."
        exit 1
    fi
    bfn=$(basename "$fn")
    echo "$bfn,$val" >>"$outFile"
done

shopt -u nullglob             # restore default globbing
