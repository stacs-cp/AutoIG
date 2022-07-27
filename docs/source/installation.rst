Installation
-------------------

AutoIG makes use of several softwares, including:

    - The `Essence pipeline`_: a constraint modelling toolchain developed by our Constraint Programming group at University of St Andrews and University of York. The pipeline supports modelling a combinatorial optimisation problem as a constraint model. Starting with an abstract specification of a constraint problem (written in Essence_), the pipeline can perform the modelling and solving phases efficiently and automatically via the constraint modelling and reformulation tools `Conjure`_ [AFGJ22]_ and `Savile Row`_ [NAGJ17]_. 

    - The automated algorithm configurator `irace`_ [LDCB16]_: irace is a general-purpose automated tool for configuring parameters of algorithms. 

    - The `MiniZinc`_ [NSBB07]_ toolchain: a constraint modelling toolchain developed at Monash University, in collaboration with Data61 Decision Sciences and the University of Melbourne. MiniZinc supports `several solvers`__ via their FlatZinc interfaces. AutoIG uses MiniZinc to access those solvers and generate benchmarking instances for them.

    - `runsolver`_ [Rous11]_: a tool for controlling solver execution (to ensure that memory and time limit are respected).

.. _`Essence pipeline`: https://constraintmodelling.org/
.. _Essence: https://conjure.readthedocs.io/en/latest/essence.html
.. _`Conjure`: https://github.com/conjure-cp/conjure
.. _`Savile Row`: https://savilerow.cs.st-andrews.ac.uk/
.. _`irace`: https://iridia.ulb.ac.be/irace/
.. _`MiniZinc`: https://www.minizinc.org/
.. __: https://www.minizinc.org/software.html
.. _`runsolver`: https://content.iospress.com/articles/journal-on-satisfiability-boolean-modeling-and-computation/sat190083

To install all softwares, a bash script is provided in ``bin/install-all.sh``. The script will download and install all softwares into ``bin/``. 

After installation, please set the environment variables accordingly by running the following line at the beginning of each bash session:

.. code-block:: rst

    . bin/set-path.sh


**References**

.. [AFGJ22] Akgün, Ö., Frisch, A.M., Gent, I.P., Jefferson, C., Miguel, I. and Nightingale, P., 2022. Conjure: Automatic Generation of Constraint Models from Problem Specifications. Artificial Intelligence, p.103751.

.. [NAGJ17] Nightingale, P., Akgün, Ö., Gent, I.P., Jefferson, C., Miguel, I. and Spracklen, P., 2017. Automatically improving constraint models in Savile Row. *Artificial Intelligence*, **251**, pp.35-61.

.. [LDCB16] López-Ibáñez, M., Dubois-Lacoste, J., Cáceres, L.P., Birattari, M. and Stützle, T., 2016. The irace package: Iterated racing for automatic algorithm configuration. *Operations Research Perspectives*, **3**, *pp.43-58*.

.. [NSBB07] Nethercote, N., Stuckey, P.J., Becket, R., Brand, S., Duck, G.J. and Tack, G., 2007, September. MiniZinc: Towards a standard CP modelling language. *In International Conference on Principles and Practice of Constraint Programming (pp. 529-543)*. Springer, Berlin, Heidelberg.

.. [Rous11] Roussel, O., 2011. Controlling a solver execution with the runsolver tool. Journal on Satisfiability, *Boolean Modeling and Computation*, **7(4)**, *pp.139-144*.