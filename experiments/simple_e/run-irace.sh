#!/bin/bash

irace --seed 42 --scenario /AutoIG/scripts/scenario.R --parameter-file params.irace --train-instances-file instances --exec-dir ./ --max-experiments 180 --target-runner /AutoIG/scripts/target-runner --debug-level 2
