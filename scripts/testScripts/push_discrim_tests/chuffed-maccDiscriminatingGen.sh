#!/bin/bash
# Tests discriminating instance generation with Macc problem,  using full generator, and the Chuffed solver.
echo $AUTOIG
mkdir -p "$AUTOIG/experiments/macc-discrim-small-gen"
cd "$AUTOIG/experiments/macc-discrim-small-gen"
python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver picat --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5
bash "$AUTOIG/experiments/macc-discrim-small-gen/run.sh"
