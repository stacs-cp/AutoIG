#!/bin/bash

# Testing graded instance generation for the Macc problem using its small generator with the cpsat solver"
mkdir -p "$AUTOIG/experiments/vessel_loading"
cd "$AUTOIG/experiments/vessel_loading"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/vessel-loading/generator.essence" --problemModel "$AUTOIG/data/models/problem.essence" --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver cpsat --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 3

bash "$AUTOIG/experiments/vessel_loading/run.sh"
