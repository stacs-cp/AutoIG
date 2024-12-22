#!/bin/bash
# This script is used to ensure that the or-tools solver can be found by Conjure:
# Chuffed binary being searched for is called: fzn-cp-sat
DATA_DIR=essence_testing_data
ls
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=or-tools
rm -r conjure_solve-tests/conjure-output
