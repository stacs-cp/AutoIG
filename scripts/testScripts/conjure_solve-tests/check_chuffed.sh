#!/bin/bash
DATA_DIR=../essence_testing_data
ls $DATA_DIR
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=chuffed
