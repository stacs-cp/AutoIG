# Description

This is a directory which contains scripts to test various parts of AutoIG. Its test scripts can both be run manually by a user, or automatically when called by a GitHub aciton in the AutoIG CI pipeline.

Each `test script` calls a corresponding folder of `run files`. Each `run file` is a full setup and run of AutoIG, and the `test script` scans the output caused by running the experiment ran by each `run file`, ensuring it contains all of the provided lines. To keep test results consistent, each currently made `run file` uses the same parameters as explained further on, but a different solver. Solvers tested to be functional currently include: chuffed, cpsat, gecode, picat, and yuck. The lines being searched for are manually set in each script itself, in a `lines` array towards the top of each script. Each script operates by iterating through all `run files` in each tests directory, so additional `run files` with different configurations/runs of AutoIG can be directly added with no further adjustments necessary.

For example, `check_push` would call all of the `run files` in `/push_graded_tests`, then insure that the output of every run file contained all lines specified in an array within the `check_push` script.

After a test script is run, the script also outputs the number of passed run files / the number of failed run files, as well as time taken to run all of them. Whenever a line is failed to be found, the script also outputs which line (or lines) weren't found to cause this issue.

## Manual Run Instructions

To run any of these scripts, ensure that project paths are set up as described in the general README, then make a call to the script you wish to call. For example: `bash check`pr.sh`.

Each of these test scripts call run script within its corresponding folder of `pr_discrim_tests`, `pr_graded_tests`, `push_discrim_tests`, or `push_graded_tests`. Each run script sets up an AutoIG experiment and runs it.

## Script Descriptions

All currently created tests use the macc problem in data/models/macc, with each test script testing that macc works with every supported solver.

In the context of usage by the pipeline, some runs are meant to be called on PRs, and are more intensive, being done with the full macc generator. Some are meant to be called on pushes to any branch and are less intensive, being done with the small macc generator instead.

Provided Scripts include:

- `check_conjure`: test container environment is set correctly, and Conjure is able to find location of all needed solver binaries.
- `check_pr_discrim`: test discriminating instance generation with full macc generator.
- `check_pr`: test graded instances with full macc generator.
- `check_push_discrim`: test discriminating instances with small macc generator.
- `check_push`: test graded instances with small macc generator.

Example contents of a test script may look like:

## Within push_discrim_tests:

`cd "AutoIG/experiments/macc-graded"`

`python3 "\$AUTOIG/scripts/setup.py --generatorModel \$AUTOIG/data/models/macc/generator-small.essence --problemModel \$AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags=\"-f\" --maxEvaluations 180 --genSolverTimeLimit 5"`

`bash "run.sh"`
