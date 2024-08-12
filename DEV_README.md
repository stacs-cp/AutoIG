This is a summary of the commands to run the project in a Docker container.

## Docker Build And Run Commands

docker build --platform linux/amd64/v2 -t conjure_clone_image .

docker run -it conjure_clone_image /bin/bash

## Commands To Run Inside Docker Container For Quick Start Example

. bin/set-path.sh

AUTOIG=$(pwd)

mkdir -p experiments/macc-graded/

cd experiments/macc-graded/

python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5

## To Run The Generated Bash Script

bash run.sh
