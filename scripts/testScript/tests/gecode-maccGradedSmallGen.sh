#!/bin/bash

# avoids having an error if directory already exists
echo "the variable is: "
ls
echo $AUTOIG
mkdir -p "$AUTOIG/experiments/macc-graded-small-gen"
cd "$AUTOIG/experiments/macc-graded-small-gen"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/macc/generator-small.essence" --problemModel "$AUTOIG/data/models/macc/problem.mzn" --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver gecode --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 3

bash "$AUTOIG/experiments/macc-graded-small-gen/run.sh"
