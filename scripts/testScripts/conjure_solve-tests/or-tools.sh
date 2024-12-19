#!/bin/bash
DATA_DIR=essence_testing_data
ls
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=or-tools
rm -r conjure_solve-tests/conjure-output
