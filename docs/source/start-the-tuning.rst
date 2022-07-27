Start the tuning
=====================================================================================

After setting up a graded or discriminating experiment using the script ``scripts/setup.py``, we can start the instance generation process with irace by simply running the ``run.sh`` script in the experiment folder:

.. code-block:: console

    bash run.sh

This script will start irace and when the instance generation process is finished, it will extract the list of graded/discriminating instances from the raw outputs and their detailed results. A summary of results will be printed out to the screen. 

Below is an example summary for the MACC graded experiment:

.. code-block:: rst

    Total #runs: 171
    Total #instances generated: 104

    #graded instances: 54 (/114 runs)
    #too difficult instances: 50 (/50 runs)

In the example above, 171 evaluations have been used during the instance generation process. There are 104 (unique) candidate instances generated, among them there are 54 graded instances and 50 instances where Chuffed cannot solve within the given (tiny) time limit. Different generator configurations may produce the same candidate instances. The number of runs shown in the brackets indicate the total number of candidate instances including duplicated ones (114 for graded instances and 50 for difficult instances).

And an example summary for the MACC discriminating experiment:

.. code-block:: rst

    Total #runs: 175
    Total #instances generated: 91

    #instances where the base solver wins: 8 (/62 runs)
    #too easy instances for the base solver: 6 (/25 runs)
    #instances where the favoured solver wins: 1 (/1 runs)
    #too difficult instances for the favoured solver: 76 (/77 runs)

The list of graded/discriminating instances and their detailed results are available at ``graded-instances-info.csv`` and ``discriminating-instances-info.csv``, located in the same folder of the experiments. For detailed results of all evaluations during the whole instance generation process, please checkout ``detailed-output.json``, where each line coressponds to a generator configuration evaluation.

.. note::
    The ``detailed-output`` folder contains all outputs and temporary files created during the instance generation process. This folder can get heavy pretty soon, therefore, after the instance generation process is finished and you have extracted all graded/discriminating instances out of it, this folder can be safely removed. The reason why we do not remove this folder automatically is because sometime the tuning can crash after running for a while due to some bugs/issues with the solvers themselves, or simply because we are out of computational resources (e.g., a job run on a cluster computer is killed due to hitting the time limit allowed). In such cases, we want to resume the experiments from where it was before the termination instead of having to re-run from the start. If the ``detailed-output`` folder is available, AutoIG will automatically read results in that folder and resume the experiment when users call ``run.sh`` again.

..
    ``out-<generator_configuration_id>-<random_seed>``: irace creates a number of generator configurations (generator instances). We get a candidate instance from solving a generator instance with a particular random seed. Those ``out-*-*`` files record all commands, outputs and results of each generator instance solving. The last line is the most important one showing the results of the run, including information such as the total running time, results of the generator instance solving, the evaluation of the candidate instance obtained (if one is generated). If the tuning crashes, those ``out-*-*`` are the place to look into to see what the issues are.
        - ``gen-inst-<generator_configuration_id>.param``: