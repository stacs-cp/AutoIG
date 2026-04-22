name="irace"
version="4.4.1"

echo ""
echo "============= INSTALLING $name ==================="
echo "$name version: $version"

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# check if R is installed
if ! [ -x "$(command -v R)" ]; then
    echo "ERROR: R must be installed first. See https://www.r-project.org/ for how to install R."
    exit 1
fi

url="https://cran.r-project.org/src/contrib/irace_4.4.1.tar.gz"

Rscript -e "install.packages(c('https://cran.r-project.org/src/contrib/R6_2.6.1.tar.gz', 'https://cran.r-project.org/src/contrib/data.table_1.18.2.1.tar.gz', 'https://cran.r-project.org/src/contrib/matrixStats_1.5.0.tar.gz', 'https://cran.r-project.org/src/contrib/spacefillr_0.4.0.tar.gz', 'https://cran.r-project.org/src/contrib/digest_0.6.39.tar.gz'), lib='$BIN_DIR', repos=NULL, type='source')"
export R_LIBS=$BIN_DIR/:$R_LIBS
Rscript -e "install.packages('$url', type='source')"

# pushd $BIN_DIR

# mkdir -p $name

# SOURCE_DIR="$name-source"
# mkdir -p $SOURCE_DIR

# pushd $SOURCE_DIR
# wget $url
# tar zxf irace_4.4.1.tar.gz
# # cp $BIN_DIR/irace-source.zip ./
# # unzip irace-source.zip
# #wget https://cran.r-project.org/src/contrib/R6_2.5.1.tar.gz
# #tar zxf R6_2.5.1.tar.gz
# #wget https://cran.r-project.org/src/contrib/data.table_1.14.2.tar.gz
# #tar zxf data.table_1.14.2.tar.gz
# #R CMD INSTALL -l $BIN_DIR/ R6
# cp $BIN_DIR/R-packages.R ./
# OS=$(uname)
# if [ "$OS" == "Darwin" ]; then
#     sed -i "" "s#<BIN_DIR>#$BIN_DIR#g" R-packages.R
# elif [ "$OS" == "Linux" ]; then
#     sed -i "s#<BIN_DIR>#$BIN_DIR#g" R-packages.R
# else
#     echo "Cannot determine your OS, uname reports: ${OS}"
#     exit 1
# fi
# Rscript R-packages.R
# export R_LIBS=$BIN_DIR/:$R_LIBS
# R CMD INSTALL -l $BIN_DIR/ "irace_4.4.1.tar.gz"
# popd

# rm -rf $SOURCE_DIR

# popd
