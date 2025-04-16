#!/bin/bash

#set -x # echo commands
# set -E # exit on any non-zero commands
name="runsolver"

OS=$(uname)
if [ "$OS" != "Linux" ]; then
    echo "${name} only supports Linux, sorry :/"
    exit 1
fi

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

url="https://www.cril.univ-artois.fr/~roussel/runsolver/runsolver-3.4.0.tar.bz2"

pushd $BIN_DIR
wget $url
tar xvjf *.bz2

pushd $name/src
make

if test -f "${name}"; then
    echo "Installation seems to have run successfully."
else
    echo "============= Installation has NOT been successful!!! ==================="
fi
