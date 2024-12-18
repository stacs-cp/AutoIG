#!/bin/bash
name="picat"
version="9.2"

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

# minizinc must be installed before picat
if [ $contFlag ]; then
    echo "using setup for container"
    if [ ! -d "$CONTAINER_BIN_DIR/share/minizinc" ]; then
        echo "ERROR: Container Minizinc not setup correctly"
        exit 1
    else
        echo "MiniZinc in .local/bin found correctly. "
    fi
elif [ ! -d "$BIN_DIR/minizinc/share/minizinc" ]; then
    echo "ERROR: minizinc must be installed in $BIN_DIR first. You can use the install-minizinc.sh script for the installation."
    exit 1
fi

pushd $BIN_DIR

OS=$(uname)
if [ "$OS" == "Darwin" ]; then
    url="http://picat-lang.org/download/picat316_macx.tar.gz"
elif [ "$OS" == "Linux" ]; then
    url="http://picat-lang.org/download/picat316_linux64.tar.gz"
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

mkdir -p $name

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR

# download picat binary and lib
wget $url
tar zxf $(ls picat*.gz)
d="Picat"
cp -r $d/lib $d/picat $BIN_DIR/$name/ # TODO: check the macos version

# download picat flatzinc intepreter
wget https://github.com/nfzhou/fzn_picat/archive/refs/heads/main.zip
unzip main.zip
#wget https://github.com/hakank/fzn_picat/archive/6a12883ace8ab7b4cf94419af5a40139c105a005.zip; unzip 6a12883ace8ab7b4cf94419af5a40139c105a005.zip; mv fzn_picat-6a12883ace8ab7b4cf94419af5a40139c105a005 fzn_picat-main/

if [ "$contFlag" = true ]; then
    # Case for if this is installed using the container
    echo "Copying Picat to container inst of minizinc"
    cp -r fzn_picat-main/mznlib $CONTAINER_BIN_DIR/share/minizinc/$name
    cp fzn_picat-main/*.pi $CONTAINER_BIN_DIR/$name/
else
    echo "Copying Picat to bin inst of minizinc"

    # Case for if this installed for AutoIG directly in Linux, not using the container
    cp -r fzn_picat-main/mznlib $BIN_DIR/minizinc/share/minizinc/$name
    cp fzn_picat-main/*.pi $BIN_DIR/$name/
fi

popd

rm -rf $SOURCE_DIR

if [ "$contFlag" = true ]; then
    echo "Copying Picat to container inst of minizinc config file"

    # Case for if this is installed using the container
    CONFIG_FILE="$CONTAINER_BIN_DIR/share/minizinc/solvers/$name.msc"
    cp picat.msc $CONFIG_FILE
else
    echo "Copying Picat to bin inst of minizinc config file"

    # Case for if this installed for AutoIG directly in Linux, not using the container
    CONFIG_FILE="$BIN_DIR/minizinc/share/minizinc/solvers/$name.msc"
    cp picat.msc $CONFIG_FILE
fi

# No different conditions for where MZN or solver is located
if [ "$OS" == "Darwin" ]; then
    #sed -i "" "s/<name>/$name/g" $CONFIG_FILE
    echo "TODO"
    exit 1
elif [ "$OS" == "Linux" ]; then
    sed -i "s/<name>/$name/g" $CONFIG_FILE
    sed -i "s/<version>/$version/g" $CONFIG_FILE
    #sed -i "s#<BIN_DIR>#$BIN_DIR#g" $CONFIG_FILE
    #sed -i "s#<mznlib>#$BIN_DIR/minizinc/share/minizinc/$name#g" $CONFIG_FILE

else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

popd
