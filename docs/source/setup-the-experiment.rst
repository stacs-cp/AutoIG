Setup the experiment
=====================================================================================

After preparing an instance generator model, we can start setting up an instance generation experiment for AutoIG. The setup scrip is located at ``scripts/setup.py``. 

A full list of all setup arguments can be found `here`_. Below is a list of the essential ones:

    - ``--problemModel``: path to a description of the problem we want to generate instances for, written as a constraint model in either `Essence`_ or `MiniZinc`_. Note that the model file name should be ended with either ``.essence`` or ``.mzn``.
    - ``--generatorModel``: path to a parameterised instance generator of the given problem, written as a constraint model in `Essence`_ (see: :doc:`create-an-instance-generator` for more details).
    - ``--instanceSetting``: the type of instances being generated. Must be either ``graded`` or ``discriminating`` (see: `graded/discriminating instance`_ for more details). 
    - ``--minSolverTime``: (in seconds) instances solved within less than this lower bound will be considered too trivial and will be discarded.  For discriminating instance generation, this requirement is only applied to the base solver. Default value: 0 (no lower bound).
    - ``--maxSolverTime``: (in seconds) the time limit for each solver call when solving a candidate instance.
    - ``--solver``: (graded experiments only) the solver we want to generate instances for.
    - ``--favouredSolver``: (discriminating experiments only) the favoured solver, i.e., we want to generate instances that are relatively easy for this solver.
    - ``--baseSolver``: (discriminating experiments only) the base solver, i.e., we want to generate instances that are relatively difficult for this solver.

.. _`examples for setting up an experiment`:

Examples
---------------------------

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

A full list of generated files (and folder) by the setup script is listed below:

    - ``problem.mzn`` or ``problem.essence``: a copy of the original problem specification model.
    - ``generator.essence``: a copy of the original instance generator model.
    - ``params.irace``, ``instances``, ``run-irace.sh``: files needed to call irace.
    - ``generator.eprime``: the instance generator model translated into Essence Prime language, used by the Essence pipeline when solving generator instances.
    - ``config.json``: a ``.json`` file containing all settings of the experiments.
    - ``detailed-output``: a folder containing all temporary files created during the instance generation process. See LINK for more details.
        

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

The list of files (and folder) generated by the setup script is similar to the graded experiment described above.

.. _`graded/discriminating instance`:

Graded/Discriminating instances
------------------------------------------------------------------------------------------------

AutoIG currently supports generating two types of instances: 

    - **graded instances** (for a single solver only): instances "solvable" by a given solver within [a, b] seconds, where ``a`` and ``b`` are specified by users. The lower bound ``a`` is to make sure that trivially solved instances are not included (default value: 0 seconds, i.e., no lower bound), as they are normally not very interesting for the developers of the solver. The definition of "solvable" is as follows:

        - For complete solvers: the solver returns a feasible solution or a claim of unsatisfiablity (for decision problem), or returns the optimial solution and a claim of optimality (for optimisation problems).
        - For incomplete solvers (e.g., yuck_ `[BMFP15]`_): the solver returns a feasible solution (for decision problem). In case of optimisation problems, since a proof of optimality cannot be achieved for optimisation problems, we use an external complete solver (called the *oracle*) to solve the instance to optimality (with a time limit of 1 hour) and use the obtained optimal solution as a reference. If the given solver can find a solution with the same optimal objective value, the instance is marked as "solvable" and the solving time is the first time such solution is found. To minimise the overhead of running the oracle external solver, we use `Google OR-Tools`_ as the oracle, as this is a very strong solver (indicated by its several `gold medals`_ at the MiniZinc Challenges).        
    
    - **discriminating instances** (for a pair of solvers): instances that are easier to solve by one solver (the **favoured solver**) compared to the other (the **based solver**). AutoIG will try to search for instances that maximise the ratio between performance of the **favoured solver** and the **base solver**.

        - The performance of the two solvers are measured using the `MiniZinc complete scoring method`_, which takes into account both solution quality and running time. The total scores of both solver on an instance always add up to 1. The higher the score, the better a solver performs compared to the other. 
        - The ratio ``score(favouredSolver)/score(baseSolver)`` is called the **discriminating power** of the instance. AutoIG will return instances where this ratio is larger than 1.

.. _`here`:

All setup arguments
------------------------------------------------------------------------------------------------

**General settings:**

    - ``--runDir``: directory where the experiment will be run. All data prepared by the setup script will be put in this folder. Default: ``./`` (current folder)
    - ``--problemModel``: path to a description of the problem we want to generate instances for, written as a constraint model in either `Essence`_ or `MiniZinc`_. Note that the model file name should be ended with either ``.essence`` or ``.mzn``.
    - ``--generatorModel``: path to a parameterised instance generator of the given problem, written as a constraint model in `Essence`_ (see: :doc:`create-an-instance-generator` for more details).
    - ``--seed``: random seed for the experiment (used by irace). Default: 42
    - ``--maxEvaluations``: AutoIG running budget, i.e., the total number of evaluations being used by irace during the tuning process. Each evaluation correspond to solving a generator instance, getting an instance out of it (if possible), evaluating the quality of that instance, and returning a score back to irace. Default: 2000
    - ``--nCores``: the number of parallel proccesses irace can use during the tuning. If you have parallel resources available, utilising this option can generally speed up the total running time (walltime) a lot. Default: 1

**Generator instance settings:** 

Each generator instance is solved using the Essence pipeline, which consists of three steps: (i) translating the generator instance (in Essence) to a lower-level modelling language called Essence Prime with `Conjure`_; (ii) reformulating and translating the generator instance in Essence Prime to the input accepted by the constraint solver `minion`_ with `Savile Row`_; (iii) solving the generator instance with `minion`_ and getting a candidate problem instance out of it (if possible). The settings listed here are for the solving process of each generator instance.

    - ``--genSRTimeLimit``: (in seconds) Savile Row time limit. Default: 300
    - ``--genSRFlags``: Savile Row flags. Default: ``-S0 -no-bound-vars``
    - ``--genSolver``: the solver being used for solving each generator instance. Currently only minion is supported.
    - ``--genSolverTimeLimit``: (in seconds) solving time limit for minion. Default: 300
    - ``--genSolverFlags``: minion flags. Default: ``-varorder domoverwdeg -valorder random``
    - ``--repairModel``: path to a repair model. If none provided, framework will check experiment run directory for one. Default: None. 

.. note:: 
    We suggest keeping all generator settings as their default values, although the time limits for Savile Row and minion can be increased/decreased depending on applications.

**Candidate instance settings** 

*(for both graded and discriminating experiments)*

    - ``--instanceSetting``: the type of instances being generated. Must be either ``graded`` or ``discriminating`` (see: `graded/discriminating instance`_ for more details). 
    - ``--instanceValidTypes``: if you are only interested in SAT instances (or UNSAT instances), please set this argument to ``sat`` (or ``unsat``). Default: ``all`` (both SAT and UNSAT instances are accepted by AutoIG).
    - ``--minSolverTime``: (in seconds) instances solved within less than this lower bound will be considered too trivial and will be discarded.  For discriminating instance generation, this requirement is only applied to the base solver. Default value: 0 (no lower bound).
    - ``--maxSolverTime``: (in seconds) the time limit for each solver call when solving a candidate instance.
    - ``--SRTimeLimit``: (in seconds) the time limit for Savile Row while soving generated instances (only applicable for essence problem models).
    - ``--nRunsPerInstance``: number of runs a solver is being evaluated per candidate instance. To evaluate the quality of a candidate instance, results will be aggregated across all runs: for graded experiment the median of the results will be used, while for discriminating experiment the MiniZinc complete scores are calculated per run and all scores are summed up before calculating the discriminating power. Default: 1

*(for graded experiments only)*

    - ``--solver``: the solver we want to generate instances for.
    - ``--solverFlags``: extra flags for the solver.

*(for discriminating experiments only)*

    -- ``--favouredSolver``: the favoured solver, i.e., we want to generate instances that are relatively easy for this solver.
    -- ``--baseSolver``: the base solver, i.e., we want to generate instances that are relatively difficult for this solver.
    -- ``--favouredSolverFlags``: extra flags for the favoured solver.
    -- ``--baseSolverFlags``: extra flags for the base solver.


.. _yuck: https://github.com/informarte/yuck
.. _`[BMFP15]`: G. Björdal, J.-N. Monette, P. Flener, and J. Pearson. A Constraint-Based Local Search Backend for MiniZinc. *Constraints*, *20(3):325-345*, 2015.
.. _`Google OR-Tools`: https://developers.google.com/optimization
.. _`gold medals`: https://www.minizinc.org/challenge.html
.. _`MiniZinc complete scoring method`: https://www.minizinc.org/challenge2021/rules2021.html\#assessment
.. _`Essence`: https://conjure.readthedocs.io/en/latest/essence.html
.. _`MiniZinc`: https://www.minizinc.org/doc-2.6.4/en/index.html
.. _`minion`: https://constraintmodelling.org/minion/
.. _`Essence pipeline`: https://constraintmodelling.org/
.. _`Conjure`: https://github.com/conjure-cp/conjure
.. _`Savile Row`: https://savilerow.cs.st-andrews.ac.uk/
.. _`irace`: https://iridia.ulb.ac.be/irace/
.. _`Chuffed`: https://github.com/chuffed/chuffed
