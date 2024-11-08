#!/bin/bash

irace --seed 42 --scenario /home/tudor/AutoIG/scripts/scenario.R --parameter-file params.irace --train-instances-file instances --exec-dir ./ --max-experiments 400 --target-runner /home/tudor/AutoIG/scripts/target-runner --debug-level 2
