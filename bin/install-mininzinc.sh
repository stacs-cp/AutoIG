#!/bin/bash

name="minizinc"
version="2.8.5"

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pushd $BIN_DIR

OS=$(uname)
if [ "$OS" == "Darwin" ]; then
    #url="https://github.com/MiniZinc/MiniZincIDE/releases/download/${version}/MiniZincIDE-${version}-bundled.dmg"
    echo "Using local files (minizinc-${version}-part-mac.tgz) for minizinc installation"
elif [ "$OS" == "Linux" ]; then
    url="https://github.com/MiniZinc/MiniZincIDE/releases/download/${version}/MiniZincIDE-${version}-bundle-linux-x86_64.tgz"
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

mkdir -p $name

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
if [ "$OS" == "Linux" ]; then
    wget $url
    tar zxf $(ls *.tgz)
    d=$(ls -d */)
    mv ${d}/* $BIN_DIR/$name
else
    cp $BIN_DIR/minizinc-${version}-part-mac.tgz ./
    tar zxf minizinc-${version}-part-mac.tgz
    mv Resources/minizinc Resources/bin/
    cp -r Resources/* $BIN_DIR/minizinc
fi
popd

rm -rf $SOURCE_DIR

popd
