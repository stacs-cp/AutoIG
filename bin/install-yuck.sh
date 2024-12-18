#!/bin/bash
name="yuck"
version="20210501"

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CONTAINER_BIN_DIR="/root/.local/bin"

# Check for --containerBuild flag
contFlag=false
for arg in "$@"; do
    if [ "$arg" == "--containerBuild" ]; then
        contFlag=true
        break
    fi
done

# minizinc must be installed before Yuck
if [ $contFlag ]; then
    echo "using setup for container"
    if [ ! -d "$CONTAINER_BIN_DIR/share/minizinc" ]; then
        echo "ERROR: Container Minizinc not setup correctly"
        exit 1
    fi
elif [ ! -d "$BIN_DIR/minizinc/share/minizinc" ]; then
    echo "ERROR: minizinc must be installed in $BIN_DIR first. You can use the install-minizinc.sh script for the installation."
    exit 1
fi

# These pushes should be left the same between container and regular usage, because the location of Yuck is the same only MZN location is different
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
    if [ "$contFlag" = true ]; then #Case for setting up in the container
        sed -i "s#../bin/yuck#../../../../$name/bin/yuck#g" mzn/yuck.msc
        # Replacing the paths in the mzn/yuck.msc file
        sed -i "s#.*mznlib.*#    \"mznlib\": \"$CONTAINER_BIN_DIR/share/minizinc/$name\",#g" mzn/yuck.msc
    else
        sed -i "s#../bin/yuck#../../../../$name/bin/yuck#g" mzn/yuck.msc
        # Replacing the paths in the mzn/yuck.msc file
        sed -i "s#.*mznlib.*#    \"mznlib\": \"$BIN_DIR/minizinc/share/minizinc/$name\",#g" mzn/yuck.msc
    fi
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

if [ "$contFlag" = true ]; then
    # Case for if this is installed using the container
    cp mzn/yuck.msc $CONTAINER_BIN_DIR/share/minizinc/solvers
    mv mzn/lib $CONTAINER_BIN_DIR/share/minizinc/$name
else
    # Case for if this installed for AutoIG directly in Linux, not using the container
    cp mzn/yuck.msc $BIN_DIR/minizinc/share/minizinc/solvers/
    mv mzn/lib $BIN_DIR/minizinc/share/minizinc/$name
fi

popd
popd

rm -rf $SOURCE_DIR

popd
