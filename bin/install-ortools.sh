#!/bin/bash
name="ortools"
version="9.2"

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# minizinc must be installed before ortools
if [ ! -d "$BIN_DIR/minizinc/share/minizinc" ]; then
    echo "ERROR: minizinc must be installed in $BIN_DIR first. You can use the install-minizinc.sh script for the installation."
    exit 1
fi

pushd $BIN_DIR

OS=$(uname)
if [ "$OS" == "Darwin" ]; then
    url="https://github.com/google/or-tools/releases/download/v9.2/or-tools_flatzinc_MacOsX-12.0.1_v9.2.9972.tar.gz"
elif [ "$OS" == "Linux" ]; then
    url="https://github.com/google/or-tools/releases/download/v9.2/or-tools_amd64_flatzinc_ubuntu-18.04_v9.2.9972.tar.gz"
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

rm -rf $name
mkdir -p $name

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
wget $url
tar zxf $(ls *.gz)
d=$(ls -d */)
mv ${d}/* $BIN_DIR/$name
popd

rm -rf $SOURCE_DIR

mv $BIN_DIR/$name/bin/fzn-or-tools $BIN_DIR/$name/bin/fzn-ortools

cp -r $BIN_DIR/$name/share/minizinc $BIN_DIR/minizinc/share/minizinc/$name
CONFIG_FILE="$BIN_DIR/minizinc/share/minizinc/solvers/$name.msc"
cp solver.msc $CONFIG_FILE

if [ "$OS" == "Darwin" ]; then
    sed -i "" "s/<name>/$name/g" $CONFIG_FILE
    sed -i "" "s/<version>/$version/g" $CONFIG_FILE
    sed -i "" "s#<binary>#../../../../$name/bin/fzn-$name#g" $CONFIG_FILE
    sed -i "" "s#<mznlib>#../$name#g" $CONFIG_FILE
elif [ "$OS" == "Linux" ]; then
    sed -i "s/<name>/$name/g" $CONFIG_FILE
    sed -i "s/<version>/$version/g" $CONFIG_FILE
    sed -i "s#<binary>#../../../../$name/bin/fzn-$name#g" $CONFIG_FILE
    sed -i "s#<mznlib>#../$name#g" $CONFIG_FILE

else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

popd
