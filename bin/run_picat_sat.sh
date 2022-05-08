#!/bin/bash

BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# see https://groups.google.com/g/minizinc/c/mBmQL6gXKP0 for more details
picat $BIN_DIR/picat/fzn_picat_sat.pi $*
