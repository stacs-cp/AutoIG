#!/bin/bash
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Remove chuffed from container, and use one in MZN bin
rm ~/.local/bin/fzn-chuffed

# Remove minizinc from container, use mzn one
rm ~/.local/bin/minizinc

# Remove ortools from container, use mzn one
rm ~/.local/bin/fzn-cp-sat

echo "Undeeded paths updated for Conjure"
