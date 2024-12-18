# Description

This is a directory which contains scripts to test various AutoIG runs using regex to test output

To run this, put the commands to navigate to the AutoIG experiment directory, setup the project, and run it. See the general README for further instructions on running.

The script will automatically scan the standard output, then output weather the output of each file contained the desired lines specified within the script. The lines need to exist independently in the output, not be sequential.

After all tests are run, the script also outputs the number of passed tests / the number of failed tests, as well as time taken to run all of them.

This is one of the same test script which will eventuall be integrated into the automated CI pipeline in GitHub, but can also be used manually.

An example contents of a test may look like:

## Within tests/macc-graded:

`cd "AutoIG/experiments/macc-graded"`

`python3 "\$AUTOIG/scripts/setup.py --generatorModel \$AUTOIG/data/models/macc/generator-small.essence --problemModel \$AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags=\"-f\" --maxEvaluations 180 --genSolverTimeLimit 5"`

`bash "run.sh"`

`cd "../.."`
