 # Docker Build And Run Commands in a Container

### Builds an image of <container-name> using Docker

Cache bust argument is a workaround to ensure that a fresh version of the repo is always the one cloned.
This approach still allows the steps prior to cloning in to AutoIG to be cached, saving a lot of processing power.

`docker build --build-arg CACHE_BUST=$(date +%s) -t <container-name> .`

### Runs the container of provided name specifying running with bash

`docker run --platform linux/amd64 -it <container-name> /bin/bash`

# Use of Docker Volume

Use of a Docker volume can allow the container to bind to the user's file system, and get rid of the issue of non persistant storage within the container. The only difference is in the container `run` command, every other part of the process stays the same as described above.

Using this volume also means that a user must first clone into AutoiG on their system, so that they can bind the contents of their container to it.

## To run using a volume:

`docker run --platform linux/amd64 -it -v <volume_name>:/PathToAutoIG <container-name> /bin/bash`

# Commands To Run Inside Docker Container For Quick Start Example

## Getting the environment ready: needs to be run every time the container is open

`. bin/container-set-path.sh`

`export AUTOIG=$(pwd)`

At this point, AutoIG is fully configured and ready for use as normal.

## Example sequence of commands for setting up an experiment:

### To set up for MiniZinc

### Graded Example
`mkdir -p experiments/macc-graded/`

`cd experiments/macc-graded/`

`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5`

### Discriminating Example
`mkdir -p experiments/macc-discriminating/`

`cd experiments/macc-discriminating/`

`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver or-tools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5`


### To set up for essence

#### Graded Example
For "vessel_loading" essence problem
`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/vessel-loading/generator.essence --problemModel $AUTOIG/data/models/vessel-loading/problem.essence --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5`

For "car-sequencing" essence problem
`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/car-sequencing/generator.essence --problemModel $AUTOIG/data/models/car-sequencing/problem.essence --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 300 --genSolverTimeLimit 5`

#### Discriminating Example

`python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/vessel-loading/generator.essence --problemModel $AUTOIG/data/models/vessel-loading/problem.essence --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver ortools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5` 
### To Run The Generated Bash Script

bash run.sh

# Considerations for Use of Dockerfile

The build Docker image allows for the program to be run in a container. It is worth noting though that the container could take up more storage than running AutoIG through Linux directly, as it will download dependencies within the container such as Python and R. If a users system already has these, it could be more efficient to run it directly on the system without a VM. In addition, data does not persist within the container, so it is important to save the results of AutoIG runs, perhaps with a Docker Volume. Instructions for setting up the Docker Volume are listed above.
