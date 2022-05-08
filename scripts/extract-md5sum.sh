d=$1 # path to experiment folder

outFile="$d/instance-md5sum.csv"
echo "instance,hashValue">$outFile

for fn in $(ls $d/detailed-output/inst-*.dzn)
do
    val=$(md5sum $fn | cut -d' ' -f1)
    bfn=$(basename $fn)
    echo "$bfn,$val" >>$outFile
done
