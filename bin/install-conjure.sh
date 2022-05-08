name="conjure"
url="https://github.com/conjure-cp/conjure"
#version="6977bc0"  # essence-features branch, 2021-11-22
#version="d806b9f" # master branch, 2022-01-07

echo ""
echo "============= INSTALLING $name ==================="
#echo "$name version: $version"

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pushd $BIN_DIR

mkdir -p $name 

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
git clone $url
pushd conjure
#git checkout $version
export PATH=$BIN_DIR/$name/:$PATH
BIN_DIR=$BIN_DIR/$name make install
popd
popd

rm -rf $SOURCE_DIR

# remove conjure's savilerow (savilerow should be installed later using install-savilerow.sh)
rm -rf $name/savilerow-*
rm -rf $name/lib

popd
