#!/bin/bash

# This file is used to delete the installations of some solvers no longer used within the Conjure Container.
# Conjure already pointed to binaries in AutoIG's bin, rather than .local/bin, so the ones in .local/bin no longer needed.

# Remove chuffed from container, and use one in MZN bin
rm ~/.local/bin/fzn-chuffed

# Remove minizinc from container, use one in MZN bin
rm ~/.local/bin/minizinc

# Remove ortools from container, use one in MZN bin
rm ~/.local/bin/fzn-cp-sat
