d=$1 # path to experiment folder

outFile="$d/detailed-results.json"
echo "">$outFile

for fn in $(ls $d/detailed-output/out-*)
do
    tail -n2 $fn | head -n1 >>$outFile
done
