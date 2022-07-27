outFile="detailed-results.json"
echo "">$outFile

for fn in $(ls out-*)
do
    tail -n2 $fn | head -n1 >>$outFile
done

# replace single quotes with double quotes (look nicer for json files)
sed -i "s#'#\"#g" $outFile
