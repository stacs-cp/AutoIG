**Welcome to AutoIG's documentation!**

.. _`[Github repo]`: https://github.com/stacs-cp/AutoIG


AutoIG is a tool that supports generating new instances for benchmarking solvers via the use of constraint modelling and automated algorithm configuration. The tool currently focuses on generating instances for constraint problems written in either MiniZinc_ or Essence__. 

.. __: https://conjure.readthedocs.io/en/latest/essence.html
.. _MiniZinc: https://www.minizinc.org/

AutoIG receives as input a description of a constraint problem, an instance generator (written as a constraint model), and the solver(s) (must be accessible via either the MiniZinc_ or the Essence_ toolchains) that we want to benchmark. The tool makes use of the constraint modelling pipepline Essence_ and the automated algorithm configurator irace_ to search in the parameter space of the instance generator and create valid instances with certain desirable properties: graded (for a single solver, solvable within a certain range of time by that solver); or discriminating (for a pair of solvers, easy to solve by one solver and difficult to solve by the other). 

.. _Essence: https://constraintmodelling.org/
.. _irace: https://iridia.ulb.ac.be/irace/

.. image:: docs/source/static/autoig.png
   :height: 300px
   :alt: AutoIG 
   :align: center


For more information about AutoIG and a case study demonstrating it usefulness in benchmarking solvers in a competition context, please see our paper here__.

For details on how to use AutoIG, please see the documentation_, which also include `two quick-start examples`_.

.. __: https://arxiv.org/abs/2205.14753
.. _documentation: https://autoig.readthedocs.io/en/latest/
.. _`two quick-start examples`: https://autoig.readthedocs.io/en/latest/quick-examples.html

Citation
------------------------------------
If you use AutoIG, please cite us:

.. code-block:: rst

   @inproceedings{dang2022framework,
      title={A Framework for Generating Informative Benchmark Instances},
      author={Dang, Nguyen and Akg{\"u}n, {\"O}zg{\"u}r and Espasa, Joan and Miguel, Ian and Nightingale, Peter},
      booktitle={International Conference on Principles and Practice of Constraint Programming},  
      year={2022}
   }