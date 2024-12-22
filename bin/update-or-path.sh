#!/bin/bash

# Updates the name ORtools binary is referenced as, so that AutoIG can call it properly.

BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Location of file to update:
FILE="$BIN_DIR/minizinc/share/minizinc/solvers/cpsat.msc"

# Update name field to ortools
sed -i 's/"name": "OR Tools CP-SAT"/"name": "ortools"/' "$FILE"
