#!/bin/bash
# Tests discriminating instance generation with Vessel_loading problem, and basesolver: Chuffed and favouredSolver: ortools.
echo $AUTOIG
mkdir -p "$AUTOIG/experiments/macc-discrim-gen"
cd "$AUTOIG/experiments/macc-discrim-gen"
python3 "$AUTOIG/scripts/setup.py" --generatorModel "$AUTOIG/data/models/macc/generator.essence" --problemModel "$AUTOIG/data/models/macc/problem.mzn" --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 5 --baseSolver chuffed --baseSolverFlags="-f" --favouredSolver picat --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 3
bash "$AUTOIG/experiments/macc-discrim-gen/run.sh"
