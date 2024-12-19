#!/bin/bash
DATA_DIR=../essence_testing_data
ls $DATA_DIR
conjure solve model.essence test.param --solver=chuffed
