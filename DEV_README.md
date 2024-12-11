# Docker Build And Run Commands in a Container

### Builds an image of <container-name> using Docker

`docker build -t <container-name> .`

### Runs the container of provided name specifying running with bash

`docker run --platform linux/amd64 -it <container-name> /bin/bash`

# Commands To Run Inside Docker Container For Quick Start Example

## Getting the environment ready: needs to be run every time the container is open

`. bin/container-set-path.sh`

`AUTOIG=$(pwd)`

At this point, this version of AutoIG is ready for use as normal.

## Example sequence of commands for running an experiment:

`mkdir -p experiments/macc-graded/`

`cd experiments/macc-graded/`

`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5`

### To Run The Generated Bash Script

bash run.sh

# Considerations for Use of Dockerfile

This Docker image will require a large amount of memory to be built. It is not much more than runni

TODO can also add instructions for how to add using a volume
