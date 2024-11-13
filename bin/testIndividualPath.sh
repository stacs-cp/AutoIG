#!/bin/bash

# this is a script that will never be used in deployment, is just for Vincent to use during development while trying to get the container working

# define test path
TEST_PATH="/root/.local/bin/conjure"

# checking if the file exists at the path
if [ -f "$TEST_PATH" ]; then
    echo "Conjure path added to PATH."
else
    echo "Error: Conjure path '$TEST_PATH' does not exist."
fi
