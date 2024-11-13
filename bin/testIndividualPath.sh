#!/bin/bash

# this is a script that will never be used in deployment, is just for Vincent to use during development while trying to get the container working

# define test path
# TEST_PATH="/root/.local/bin/conjure"

# checking if the file exists at the path
if [ -f "/root/.local/bin/conjure" ]; then
    echo "Conjure path found"
else
    echo "Error: Conjure path '$TEST_PATH' does not exist."
fi

if [ -f "/root/.local/bin/minion" ]; then
    echo "Minion path found"
else
    echo "Error: Minion path '$TEST_PATH' does not exist."
fi

if [ -f "/root/.local/bin/savilerow" ]; then
    echo "SR path found"
else
    echo "Error: SR path '$TEST_PATH' does not exist."
fi

# savilerow
