#!/bin/bash

# Testing graded instance generation for the Vessel problem using the chuffed solver"
mkdir -p "$AUTOIG/experiments/vessel-graded"
cd "$AUTOIG/experiments/vessel-graded"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/vessel-loading/generator.essence" --problemModel "$AUTOIG/data/models/vessel-loading/problem.essence" --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 3

bash "$AUTOIG/experiments/vessel-graded/run.sh"
