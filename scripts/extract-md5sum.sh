outFile="instance-md5sum.csv"
echo "instance,hashValue">$outFile

for fn in $(ls inst-*.dzn)
do
    if [ "$(uname)" == "Darwin" ]; then
        val=$(md5 $fn| cut -d"=" -f2 |xargs)
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        val=$(md5sum $fn | cut -d' ' -f1)
    else
        echo "Sorry, we only support Linux and MacOS at the moment"
        exit 1
    fi
    bfn=$(basename $fn)
    echo "$bfn,$val" >>$outFile
done
