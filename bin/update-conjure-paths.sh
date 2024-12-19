#!/bin/bash
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Remove chuffed from container, and use one in MZN bin
rm ~/.local/bin/fzn-chuffed

# Remove minizinc from container, use mzn one
rm ~/.local/bin/minizinc

export PATH="/AutoIG/bin/minizinc/bin:$PATH"

echo "Paths updated for Conjure"
