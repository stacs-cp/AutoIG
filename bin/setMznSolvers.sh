#!/bin/bash

name="ortools"
BIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CONTAINER_BIN_DIR="/root/.local/bin"

# Rename binary
mv $CONTAINER_BIN_DIR/lib/libortools.so.9.8.9999 $CONTAINER_BIN_DIR/lib/fzn-ortools

# Copy OR-Tools MiniZinc libraries to MiniZinc directory
cp -r $CONTAINER_BIN_DIR/share/minizinc $CONTAINER_BIN_DIR/minizinc/share/minizinc/$name

# Copy solver config
CONFIG_FILE="$BIN_DIR/minizinc/share/minizinc/solvers/$name.msc"
cp solver.msc $CONFIG_FILE
