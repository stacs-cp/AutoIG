Quick examples
----------------------------------------

AutoIG supports generating two types of instances: 
    - graded instances (for a single solver only): instances "solvable" by a given solver within [a, b] seconds, where ``a`` and ``b`` are specified by users.
    - discriminating instances (for a pair of solvers): instances that are easier to solve by one solver (the **favoured solver**) compared to the other (the **based solver**).

Below are two quick examples on how to setup and run AutoIG. For detailed explanation of the full process, please see the next sections of this documentation.

**Generating graded instances**

The following commands setup a graded instance generation experiment for the MACC problem. The solver we are interested in is `Chuffed`_. We will generate instances that can be solved by Chuffed within 2 seconds. An extra flag ``-f`` is passed to Chuffed to let it choose its own search strategy. We allow a maximum time limit of 5 seconds for minion during each generator instance's solving process. The total budget of the instance generation process is 180 evaluations. We will use a slightly modified version of the MACC generator (``data/models/macc/generator-small.essence``, where the domains for generator parameters are reduced so irace can find some graded instances within the tiny budget given.

.. code-block:: console

    cd $AUTOIG/
    mkdir -p experiments/macc-graded/
    cd experiments/macc-graded/
    python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting graded --minSolverTime 0 --maxSolverTime 5 --solver chuffed --solverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5

The setup command above will generate a number of files in ``experiments/macc-graded``, which will be used by AutoIG during the instance generation process. Users only to need to pay attention to one file: ``run.sh``. This is the script for starting the instance generation process and for collecting results afterwards. Also all outputs of the instance generation process will be in located in ``detailed-output/`` folder.

After setting up the experiment, to start the instance generation process, run:

.. code-block:: console

    bash run.sh

This script will start irace and when the instance generation process is finished, it will also extract the list of graded/discriminating instances from the raw outputs and their detailed results. A summary of results will be printed out to the screen:

.. code-block:: rst

    Total #runs: 171
    Total #instances generated: 104

    #graded instances: 54 (/114 runs)
    #too difficult instances: 50 (/50 runs)

In the example above, 171 evaluations have been used during the instance generation process. There are 104 (unique) candidate instances generated, among them there are 54 graded instances and 50 instances where Chuffed cannot solve within the given (tiny) time limit. Different generator configurations may produce the same candidate instances. The number of runs shown in the brackets indicate the total number of candidate instances including duplicated ones (114 for graded instances and 50 for difficult instances).

**Generating discriminating instances**

The following commands setup a discriminating instance generation experiment for the MACC problem. The solvers we are interested in are `Chuffed`_ and `Google OR-Tools`_. We will generate instances that favour OR-Tools (by maximising the ratio of performance between OR-Tools and Chuffed). To avoid cases where performance difference is simply due to fluctuation in time measurement, e.g., both solvers solve the instance very quickly but the ratio indicates large difference, e.g, 0.002 seconds vs 0.02 seconds (10 times difference in solving time), we can impose a minimum solving time on the base solver Chuffed. In this example AutoIG only accepts candidate instances that require at least 1 second to be solved by Chuffed. A solving time limit of 3 seconds are used for each solver. An extra flag ``-f`` is passed to both solvers. We allow a maximum time limit of 5 seconds for minion during each generator instance's solving process. The total budget of the instance generation process is 180 evaluations.


.. code-block:: console

    cd $AUTOIG/
    mkdir -p experiments/macc-discriminating/
    cd experiments/macc-discriminating/
    python $AUTOIG/scripts/setup.py --generatorModel $AUTOIG/data/models/macc/generator-small.essence --problemModel $AUTOIG/data/models/macc/problem.mzn --instanceSetting discriminating --minSolverTime 1 --maxSolverTime 3 --baseSolver chuffed --solverFlags="-f" --favouredSolver ortools --favouredSolverFlags="-f" --maxEvaluations 180 --genSolverTimeLimit 5

After setting up the experiment, to start the instance generation process, run:

.. code-block:: console

    bash run.sh

A summary of results will be printed out to the screen:

.. code-block:: rst

    Total #runs: 175
    Total #instances generated: 91

    #instances where the base solver wins: 8 (/62 runs)
    #too easy instances for the base solver: 6 (/25 runs)
    #instances where the favoured solver wins: 1 (/1 runs)
    #too difficult instances for the favoured solver: 76 (/77 runs)

.. note::
    The list of graded/discriminating instances and their detailed results are available at ``graded-instances-info.csv`` and ``discriminating-instances-info.csv``, located in the same folder of the experiments. For detailed results of all evaluations during the whole instance generation process, please checkout ``detailed-output.json``, where each line coressponds to a generator configuration evaluation.

.. _`Chuffed`: https://github.com/chuffed/chuffed
.. _`Google OR-Tools`: https://developers.google.com/optimization