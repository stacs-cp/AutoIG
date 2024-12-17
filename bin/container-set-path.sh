#!/bin/bash

#
# get current script's folder
if [ -n "$ZSH_VERSION" ]; then
    BIN_DIR="$( cd "$( dirname "${(%):-%x}" )" &> /dev/null && pwd )"
elif [ -n "$BASH_VERSION" ]; then
    BIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
else
    echo "Error: only bash and zsh are supported"
    exit 1
fi

CONTAINER_BIN_DIR="/root/.local/bin"

# AutoIG
export AUTOIG="$(dirname $BIN_DIR)"

# conjure
export PATH=$CONTAINER_BIN_DIR/conjure:$PATH

# savilerow
export PATH=$CONTAINER_BIN_DIR/savilerow:$PATH

# minion
export PATH=$CONTAINER_BIN_DIR/minion:$PATH

# irace, installed seperately in AutoIG
export PATH=$BIN_DIR/irace/bin:$PATH
export R_LIBS=$BIN_DIR/:$R_LIBS


# minizinc
# export PATH=$BIN_DIR/minizinc/bin/:$PATH
# #export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BIN_DIR/minizinc/lib
# export MZN_SOLVER_PATH=$BIN_DIR/minizinc/share/minizinc/solvers
# export MZN_STDLIB_DIR=$BIN_DIR/minizinc/share/minizinc/

# minizinc from container
export PATH=$CONTAINER_BIN_DIR/share/minizinc/:$PATH
export MZN_SOLVER_PATH=$CONTAINER_BIN_DIR/share/minizinc/solvers
export MZN_STDLIB_DIR=$CONTAINER_BIN_DIR/share/minizinc/


# ortools - installed as fzn-cp-sat in the Conjure installation. 
export PATH=$CONTAINER_BIN_DIR/fzn-cp-sat/:$PATH


# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BIN_DIR/ortools/lib
# This installation could be wrong, needs further testing as there are numerous options
export LD_LIBRARY_PATH=$CONTAINER_BIN_DIR/lib/libortools.so.9.8.9999:$LD_LIBRARY_PATH

# yuck
export PATH=$BIN_DIR/yuck/bin/:$PATH

# picat
export PATH=$BIN_DIR/picat/:$PATH

# runsolver
export PATH=$BIN_DIR/runsolver/src/:$PATH

$BIN_DIR"/setMznSolvers.sh" 
