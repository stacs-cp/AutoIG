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


export PREFIX="$HOME/.local"
mkdir -p "$PREFIX"/{bin,include,lib}

export C_INCLUDE_PATH="$PREFIX/include:$C_INCLUDE_PATH"
export CPLUS_INCLUDE_PATH="$PREFIX/include:$CPLUS_INCLUDE_PATH"
export LIBRARY_PATH="$PREFIX/lib:$LIBRARY_PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:$LD_LIBRARY_PATH"
export PATH="$PREFIX/bin:$PATH"

pushd "/tmp"
apt-get download libnuma-dev libnuma1
dpkg -x libnuma-dev*.deb "$PREFIX"
dpkg -x libnuma1*.deb "$PREFIX"

cp -r "$PREFIX"/usr/include/* "$PREFIX/include/"
find "$PREFIX/usr/lib" -type f \( -name "libnuma.so*" -o -name "libnuma.a" \) -exec cp {} "$PREFIX/lib/" \;
find "$PREFIX/usr/lib" -type l \( -name "libnuma.so*" \) -exec cp -d {} "$PREFIX/lib/" \;

popd

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

url="https://www.cril.univ-artois.fr/~roussel/runsolver/runsolver-3.4.1.tar.bz2"

pushd $BIN_DIR
wget $url
tar xvjf *.bz2

pushd $name/src
sed -i '/^CFLAGS=/ s/$/ -fpermissive/' Makefile
make

if test -f "${name}"; then
    echo "Installation seems to have run successfully."
else
    echo "============= Installation has NOT been successful!!! ==================="
fi
