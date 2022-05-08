# NOTES: minion & chuffed & cadical will also be installed (using binaries provided by savilerow)
name="savilerow"
version="1.9.1"  # release version on Sep 11, 2021


echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pushd $BIN_DIR

OS=$(uname)
if [ "$OS" == "Darwin" ]; then
    OS_NAME="mac"
elif [ "$OS" == "Linux" ]; then
    OS_NAME="linux"
else
    echo "Cannot determine your OS, uname reports: ${OS}"
    exit 1
fi

sr="savilerow-${version}-${OS_NAME}"
url="https://savilerow.cs.st-andrews.ac.uk/${sr}.tgz" 

mkdir -p $name 

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
wget $url
tar zxf ${sr}.tgz
pushd ${sr}
bash compile.sh
chmod +x savilerow
cp -r savilerow savilerow.jar lib/ $BIN_DIR/$name
for solver in minion
do
    mkdir -p $BIN_DIR/$solver
    cp bin/*$solver* $BIN_DIR/$solver
done
popd
popd

rm -rf $SOURCE_DIR

popd
