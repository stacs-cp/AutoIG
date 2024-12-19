#!/bin/bash
DATA_DIR=essence_testing_data
ls
ls $DATA_DIR
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=chuffed
rm -r conjure_solve-tests/conjure-output
