#!/bin/bash
# This script is used to ensure that the kissat solver can be found by Conjure:
# Chuffed binary being searched for is called: kissat
DATA_DIR=essence_testing_data
ls
ls $DATA_DIR
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=kissat
rm -r conjure_solve-tests/conjure-output
