#!/bin/bash

# start the instance generation process with irace 
bash run-irace.sh

# extract output
pushd detailed-output
bash $AUTOIG/scripts/read-output-files.sh
bash $AUTOIG/scripts/extract-md5sum.sh
popd

# collect results and statistics 
python $AUTOIG/scripts/collect_results.py ./
cp detailed-output/detailed-results.json ./
