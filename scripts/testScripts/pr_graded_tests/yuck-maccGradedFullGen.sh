#!/bin/bash

# Testing graded instance generation for the Macc problem using its full generator with the yuck solver"
mkdir -p "$AUTOIG/experiments/macc-graded-gen"
cd "$AUTOIG/experiments/macc-graded-gen"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/macc/generator.essence" --problemModel "$AUTOIG/data/models/macc/problem.mzn" --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver yuck --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 3

bash "$AUTOIG/experiments/macc-graded-gen/run.sh"
