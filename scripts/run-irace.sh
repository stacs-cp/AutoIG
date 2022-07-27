#!/bin/bash

irace --seed <seed> --scenario <scenario> --parameter-file params.irace --train-instances-file instances --exec-dir ./ --max-experiments <maxExperiments> --target-runner <targetRunner> --debug-level 2
