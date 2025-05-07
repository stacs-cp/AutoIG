#!/bin/bash

# Testing graded instance generation for the Macc problem using its small generator with the chuffed solver"
mkdir -p "$AUTOIG/experiments/vessel_loading"
cd "$AUTOIG/experiments/vessel_loading"
python3 "python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/vessel-loading/generator.essence --problemModel $AUTOIG/data/models/vessel-loading/problem.essence --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver ortools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5"
bash "$AUTOIG/experiments/vessel_loading/run.sh"
