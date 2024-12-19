#!/bin/bash
DATA_DIR=../essence_testing_data
conjure solve $DATA_DIR/model.essence $DATA_DIR/test.param --solver=or-tools
