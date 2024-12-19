#!/bin/bash

echo $AUTOIG
mkdir -p "$AUTOIG/experiments/macc-discrim-gen"
cd "$AUTOIG/experiments/macc-discrim-gen"
python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver ortools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5
bash "$AUTOIG/experiments/macc-discrim-gen/run.sh"
