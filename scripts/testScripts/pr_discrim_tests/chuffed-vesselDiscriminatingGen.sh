#!/bin/bash

# Testing graded instance generation for the Vessel Loading problem using its small generator with the chuffed solver"
mkdir -p "$AUTOIG/experiments/vessel_loading_discrim"
cd "$AUTOIG/experiments/vessel_loading_discrim"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/vessel-loading/generator.essence" --problemModel "$AUTOIG/data/models/vessel-loading/problem.essence" --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 20 --baseSolver chuffed --baseSolverFlags="-f" --favouredSolver or-tools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 200
bash "$AUTOIG/experiments/vessel_loading_discrim/run.sh"
