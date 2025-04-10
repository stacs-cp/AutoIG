name="irace"
version="3.4.1"

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# check if R is installed
if ! [ -x "$(command -v R)" ]; then
    echo "ERROR: R must be installed first. See https://www.r-project.org/ for how to install R."
    exit 1
fi

url="https://cran.r-project.org/src/contrib/irace_3.4.1.tar.gz"

pushd $BIN_DIR

mkdir -p $name 

SOURCE_DIR="$name-source"
mkdir -p $SOURCE_DIR

pushd $SOURCE_DIR
#wget $url
#tar zxf $(ls *.gz)
cp $BIN_DIR/irace-source.zip ./
unzip irace-source.zip
#wget https://cran.r-project.org/src/contrib/R6_2.5.1.tar.gz
#tar zxf R6_2.5.1.tar.gz


# data.table no longer used, removed redundant dependency
# wget https://cran.r-project.org/src/contrib/data.table_1.14.2.tar.gz
# tar zxf data.table_1.14.2.tar.gz
#R CMD INSTALL -l $BIN_DIR/ R6
#cp $BIN_DIR/R-packages.R ./
#OS=$(uname)
#if [ "$OS" == "Darwin" ]; then
#    sed -i "" "s#<BIN_DIR>#$BIN_DIR#g" R-packages.R
#elif [ "$OS" == "Linux" ]; then
#    sed -i "s#<BIN_DIR>#$BIN_DIR#g" R-packages.R
#else
#    echo "Cannot determine your OS, uname reports: ${OS}"
#    exit 1
#fi
#Rscript R-packages.R
#export R_LIBS=$BIN_DIR/:$R_LIBS
#R CMD INSTALL -l $BIN_DIR/ irace
popd

rm -rf $SOURCE_DIR

popd
