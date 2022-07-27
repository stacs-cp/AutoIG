outFile="instance-md5sum.csv"
echo "instance,hashValue">$outFile

for fn in $(ls inst-*.dzn)
do
    val=$(md5sum $fn | cut -d' ' -f1)
    bfn=$(basename $fn)
    echo "$bfn,$val" >>$outFile
done
