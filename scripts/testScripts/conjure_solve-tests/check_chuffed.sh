#!/bin/bash
# This script is used to ensure that the Chuffed solver can be found by Conjure:
# Chuffed binary being searched for is called: fzn-chuffed
DATA_DIR=essence_testing_data
ls
ls $DATA_DIR
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=chuffed
rm -r conjure-output
