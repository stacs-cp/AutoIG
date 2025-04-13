#!/bin/bash
name="yuck"
version="20210501"

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

url="https://github.com/informarte/yuck/releases/download/20210501/yuck-${version}.zip"

mkdir -p $name

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
wget $url --no-check-certificate
d="yuck-${version}"
unzip $d.zip
pushd $d
mv bin/ lib/ doc/ $BIN_DIR/$name
OS=$(uname)
if [ "$OS" == "Darwin" ]; then
    sed -i "" "s#../bin/yuck#../../../../$name/bin/yuck#g" mzn/yuck.msc
    sed -i "" "s#.*mznlib.*#    \"mznlib\": \"../$name\",#g" mzn/yuck.msc
elif [ "$OS" == "Linux" ]; then
    sed -i "s#../bin/yuck#../../../../$name/bin/yuck#g" mzn/yuck.msc
    sed -i "s#.*mznlib.*#    \"mznlib\": \"$BIN_DIR/minizinc/share/minizinc/$name\",#g" mzn/yuck.msc
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

cp mzn/yuck.msc $BIN_DIR/minizinc/share/minizinc/solvers/
mv mzn/lib $BIN_DIR/minizinc/share/minizinc/$name
popd
popd

rm -rf $SOURCE_DIR

popd
