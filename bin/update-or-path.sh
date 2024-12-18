#!/bin/bash

# Location of file to update:
FILE="/AutoIG/bin/minizinc/share/minizinc/solvers/cpsat.msc"

#update name field to ortools
sed -i 's/"name": "OR Tools CP-SAT"/"name": "ortools"/' "$FILE"
# Verify  change
if grep -q '"id": "cpsat"' "$FILE"; then
    echo "Sucesfully updated."
else
    echo "Failed to update or couldn't find"
    exit 1
fi
