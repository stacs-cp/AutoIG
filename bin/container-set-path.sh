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

# AutoIG
export AUTOIG="$(dirname $BIN_DIR)"

# conjure
export PATH=/root/.local/bin/conjure:$PATH

# savilerow
export PATH=/root/.local/bin/savilerow:$PATH

# minion
export PATH=/root/.local/bin/minion:$PATH

# irace
export PATH=$BIN_DIR/irace/bin:$PATH
export R_LIBS=$BIN_DIR/:$R_LIBS

# minizinc
# export /root/.local/bin/share/minizinc:$PATH
# #export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BIN_DIR/minizinc/lib
# export MZN_SOLVER_PATH=$BIN_DIR/minizinc/share/minizinc/solvers
# export MZN_STDLIB_DIR=$BIN_DIR/minizinc/share/minizinc/





# ortools
# export PATH=$BIN_DIR/ortools/bin/:$PATH
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BIN_DIR/ortools/lib

# # yuck
# export PATH=$BIN_DIR/yuck/bin/:$PATH

# # picat
# export PATH=$BIN_DIR/picat/:$PATH

# # runsolver
# export PATH=/root/.local/bin/runsolver:$PATH