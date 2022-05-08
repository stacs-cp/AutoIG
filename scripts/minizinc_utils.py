import os
import sys
import time
import shutil
import subprocess

# correctly deal with relative imports
if __package__ is None or __package__ == '':
    import conf # uses current directory visibility
else:
    from . import conf # uses current package visibility
import tempfile


def get_minizinc_problem_type(modelFile:str):
    # TODO: this function should definitely be improved
    """
    Read a MiniZinc model and return its type (MIN/MAX/SAT)
    """
    with open(modelFile, 'rt') as f:
        lines = f.readlines()

    # remove comment lines
    lines = [l for l in lines if len(l.strip())>0 and (l.strip()[0]!='%')]

    def find_str(s):
        return len(list(filter(lambda x: s in x, lines))) > 0
    if find_str('minimize'):
        return 'MIN'
    if find_str('maximize'):
        return 'MAX'
    if find_str('satisfy'):
        return 'SAT'
    print("ERROR: cannot determine problem type of " + modelFile)
    sys.exit(1)
    return None

def is_optimisation(modelFile:str):
    """
    Check whether a minizinc model is an optimisation problem
    """
    problemType = get_minizinc_problem_type(modelFile)
    assert problemType in ['MIN','MAX','SAT']
    if problemType=='SAT':
        return False
    return True


def check_solution_consensus(modelFile:str, instFile:str, lastSol:str, solvers:list, verbose:bool=False):
    """
    Given a problem and instace solved by a specific solver, test if there is consensus on
    the validity of the solution given by the original solver.

    * modelFile: original model file
    * InstFile: original instance file
    * lastSol: map of the last solution found that has to be checked
    * solvers: list of solvers to check the solution with, represented as strings to pass to minizinc
    """

    # the procedure will be the following:
    # 1 - turn the assignments from the solution to constraints
    # 2 - add them as constraints to the original model in a newly created file
    # 3 - "instantly" solve the new problem
    # 4 - .. profit!
    valid = False # we start assuming it's invalid ...

    # slurp all the original model.
    with open(modelFile, 'rt') as f:
        lines = f.readlines()

    # get a temporary file, avoiding collisions between runs/threads.
    base, filename = os.path.split(instFile)
    tf = tempfile.NamedTemporaryFile(prefix=filename + ".solutioncheck.",
            mode='w', delete=False, suffix=".mzn", dir=base)

    # inject the solution into the model.
    if verbose: print(f"creating and solving temporary model in {tf.name}")
    for line in lines:
        # we strip the line to detect if the line is not a comment with spaces before
        if 'solve' in line and not line.strip().startswith('%'):
            # paste here
            for key, val in lastSol.items():
                tf.write(f"constraint {key} = {val}")
            tf.write(line) # now paste the solve line ...
        else:
            tf.write(line)
    tf.close()

    # for each solver, run and get the resulting status
    checked = False
    for solver in solvers:
        status, totalTime, extra = minizinc_solve(
                tf.name, instFile, solver, verbose=False, solvers_to_check=None)
        # Note that we don't care about optimisation problems. As we are only checking if a single
        # solution makes sense, we don't know (and don't want to know) if its optimal here. So
        # effectively we are turning optimisation problems into satisfiability problems.
        if status not in ["S","C"]:            
            if verbose: print(f"checked with solver: {solver} cannot seem to find a solution for whatever reason.")            
        else:
            checked = True
            assert extra['instanceType'] in ['sat','unsat']
            if extra['instanceType']=='sat':
                valid = True
                if verbose: print(f"checked with solver: {solver} agreed.")            
            else:
                if verbose: print(f"checked with solver: {solver} disagreed")
    assert checked, "ERROR: none of the checking solvers ({solvers_to_check}) can confirm results of this run ({modelFile}, {instFile})."
    os.remove(tf.name)
    return valid


def minizinc_solve(modelFile:str, instFile:str, solver:str, flags:str="-f", seed:int=None, timeLimit:float=3600.0, memLimit:int=8192, solvers_to_check:list=None, verbose=True):
    """
    Solve an instance of an optimisation problem via MiniZinc, using the runsolver binary to make it behave.

    Parameters:
        * modelFile and instFile: model and instance file paths.
        * timeLimit: WallClock time limit, in seconds (default 1h)
        * memLimit: memory limit, in MB. (default 8GB)
        * solver: minizinc solver, to be passed as a parameter to minizinc
        * flags: extra flags for minizinc
        * seed: random seed, as an integer
        * solvers_to_check: list of strings, where each string is a solver recognized by minizinc. If this
        list is not none, it will try to check the found solutions by the main call using the mentioned
        solvers.
        * verbose: makes the function print things to stdout. True by default.

    Returns:
        status (str): S/C/ERR/UNK (following MiniZinc challenge output codes (see e.g.,  https://www.minizinc.org/challenge2021/results2021.html)
            - S: a solution was found
            - C: the search was complete
            - ERR: incorrect solution / solver aborted / flattening aborted (out-of-time or out-of-memory)
            - UNK: no answer was returned within the time limit
            Note: See https://www.minizinc.org/doc-2.5.5/en/command_line.html?highlight=unknown#solution-output-options for details on how to parse minizinc output results
        totalTime (float): running time of the solver (in seconds).
        extra (dict): extra infos of the solving process, including:
            - objs (list): (optimisation problem only) each element is a pair of (time,objective), which represents the time (in seconds) and the objective value found at that point.
            - flattenStatus (str): status of the flattening process (ok/failed)
            - flattenTime (float): flattening time (in seconds)
            - instanceType (str): sat/unsat/unknown
    """
    # Bool flag to determine if we can use runsolver
    use_runsolver = sys.platform.startswith('linux')
    if solver == 'yuck':
        use_runsolver = False
    #use_runsolver = False
    runsolver_tmp_file = instFile + "." + solver + ".runsolver"

    # delay between SIGTERM and SIGKILL when timeout in runsolver
    runsolver_delay = 2

    # get problem type
    isOptimisation = is_optimisation(modelFile)

    # random seed
    seedStr = ""
    if seed is not None:
        seedStr = f"-r {seed}"

    # we store in a map the last solution.
    lastSol = {}

    # make minizinc command
    if isOptimisation:
        cmd = f"minizinc --time-limit {timeLimit * 1000} --solver {solver} -i {seedStr} {flags} {modelFile} {instFile} --output-mode dzn --output-objective -s"
    else:
        cmd = f"minizinc --time-limit {timeLimit * 1000} --solver {solver} {seedStr} {flags} {modelFile} {instFile} --output-mode dzn -s"

    # now prepend the call to runsolver if available
    if use_runsolver:
        cmd = f"runsolver -w {runsolver_tmp_file} -d {runsolver_delay} --wall-clock-limit {timeLimit} --vsize-limit {memLimit} " + cmd

    # initialise returned values
    status = None
    extra = {'objs':[], 'flattenStatus': 'failed', 'flattenTime': -1, 'instanceType':'unknown', 'answerStatus': 'unknown'}

    # start minizinc and process the output
    startTime = time.time()
    flattenAborted = True
    output = []
    if verbose: print(cmd)
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, universal_newlines=True, shell=True) as p:
        for line in p.stdout:
            output.append(line)
            # recover the objective value. Minizinc outputs this _objective
            # regardless of the naming on the optimization function
            if '_objective' in line:
                curTime = time.time() - startTime
                obj = float(line.split("=")[1].strip()[:-1])
                if verbose: print(f"{curTime:.2f}: {obj:.1f}")
                extra['objs'].append((curTime, obj))
            elif "flatTime=" in line: # recover flattening time
                flattenAborted=False
                extra['flattenTime'] = float(line.split('=')[1])
                extra['flattenStatus'] = 'ok'
            elif "=====UNKNOWN=====" in line: # what happened?
                status = "ERR"
            elif "=====ERROR=====" in line: # minizinc had an ERROR
                status = "ERR"
            elif ('=====UNSATISFIABLE=====' in line): # instance is UNSAT
                status = "C"
                extra['instanceType'] = 'unsat'
            elif ("==========" in line): # ended the search space
                status = "C"
            elif "mzn-stat: nSolutions=" in line: # check the number of solutions
                nSols = int(line.split('=')[1].strip())
                if nSols>0 and status is None:
                    status = "S"
            elif not line.startswith("%") and (" = " in line) and (line.endswith(';')): # recover solution
                lhs, rhs = line.split(" = ")
                lastSol[lhs] = rhs
            sys.stdout.flush()
    totalTime = time.time() - startTime

    # gather solver output
    output = '\n'.join([line for line in output])

    # now lets check runsolver output. We only need to care if there is no solution
    # already captured. This is the case for example in a optimisation problem where
    # we have intermediate solutions. The instance should be marked as "S" and give
    # the non-optimal solution. We also need to capture the return value for minizinc
    returncode = p.returncode
    if use_runsolver :        
        with open(runsolver_tmp_file) as f:
            for index, line in enumerate(f):
                # we check for timeouts and memouts
                if "Maximum wall clock time exceeded" in line or \
                   "Maximum VSize exceeded" in line:
                    # if runsolver kills the subprocess, no return code is reported.
                    returncode = 0 # killed
                    if len(extra['objs']) == 0:
                        status = "UNK"
                    elif status == None:
                        status = "S"
                    break
                elif "Child status" in line:
                    returncode = int(line.split(":")[1].strip())

    # now we set the status right in case we have a funny case ...
    if (returncode != 0) and (status!="ERR"):
        if ("OutOfMemoryError" in output) or \
                ("std::bad_alloc" in output) or \
                ("MiniZinc: internal error: out of memory" in output):
            status = "ERR"
        else:
            if verbose:
                print(f'ERROR: fail to run "{cmd}".')
                print(f'Return code: {returncode}.')
                print(f'Output is: {output}.\n')
            sys.exit(1)

    if status == "ERR" and (flattenAborted is False) and returncode == 0:
        status = "UNK"

    # TODO: check incorrect solution and update status accordingly
    if status in ['S','C'] and extra['instanceType']=='unknown':
        extra['instanceType']='sat'

    assert status, "ERROR: no value assigned to status"

    # Finally, do we want to check the validity of the solution given?
    if (solvers_to_check is not None) and (len(solvers_to_check)>0):
        if extra['instanceType']=='sat':
            consensus = check_solution_consensus(modelFile, instFile, lastSol, solvers_to_check, verbose=verbose)
            if consensus is False:
                if verbose: print("There is no consensus on the solution correctness")
                status = "ERR"
                extra['answerStatus'] = 'invalid'
            else:
                extra['answerStatus'] = 'valid'
        elif extra['instanceType'] == 'unsat':
            if verbose: print("There is no solution because its unsat, so won't solve that ... too expensive.")
        elif extra['instanceType'] == 'unknown':
            if verbose: print("Status is unknown, so we can't check the solution, sorry.")

    if verbose: print(status, totalTime, extra)
    return status, totalTime, extra

def has_better_objective(o1, o2, problemType):
    assert problemType in ['MIN','MAX']
    if problemType=='MIN':
        return o1<o2
    return o1>o2


def calculate_minizinc_borda_scores(status1:str, status2:str, time1:float, time2:float, problemType:str, objs1:list=[], objs2:list=[], zeroScoreWhenBothFail:bool=False):
    """
    Compute MiniZinc competition's Borda scores between two runs of two solvers.
    There are two scoring methods in this category: complete/incomplete. See Assessment section in https://www.minizinc.org/challenge2021/rules2021.html for more details.
    Important note: When both solvers fail to solve an instance, the competition scoring procedure will give a score of 0 to solver1 and a score of 1 to solver2. To give both solvers a score of 0 in such case, set zeroScoreWhenBothFail=True

    """
    assert status1 in ['S','C','ERR','UNK'], status2 in ['S','C','ERR','UNK']
    assert problemType in ['MIN','MAX','SAT']

    scores = {'complete':(), 'incomplete':()}

    def solved(status):
        return status in ['S','C']

    # for decision problems, the two scoring methods are the same
    if problemType=='SAT':

        def better_sat(s1,s2):
            if solved(s1) and not solved(s2):
                return True
            return False

        # instance is solved by only one of the two solvers
        if better_sat(status1, status2):
            scores['complete'] = scores['incomplete'] = (1,0)
        elif better_sat(status2, status1):
            scores['complete'] = scores['incomplete'] = (0,1)
        # instance is solved/unsolvable by both solvers
        else:
            # instance is solved by both solvers
            if solved(status1) and solved(status2):
                # TODO: the competition rules say "0.5 if both finished in 0s", but how to check it?
                scores['complete'] = scores['incomplete'] = (time2/(time1+time2), time1/(time1+time2))
            # instance is unsolvable for both solvers
            else:
                assert (not solved(status1)) and (not solved(status2))
                if zeroScoreWhenBothFail:
                    scores['complete'] = scores['incomplete'] = (0,0)
                else:
                    scores['complete'] = scores['incomplete'] = (0,1)

    # calculate scores for optimisation problems
    else:

        # complete scoring
        def better_optimisation_complete(s1,s2,o1,o2):
            if solved(s1) and not solved(s2):
                return True
            if (s1=='C') and (s2!='C'):
                return True
            if (s1==s2) and (s1=='S'):
                assert len(o1)>0 and len(o2)>0
                lastObj1 = o1[-1][1]
                lastObj2 = o2[-1][1]
                return has_better_objective(lastObj1, lastObj2, problemType)
            return False
        if better_optimisation_complete(status1, status2, objs1, objs2):
            scores['complete'] = (1,0)
        elif better_optimisation_complete(status2, status1, objs2, objs1):
            scores['complete'] = (0,1)
        else:
            # both solvers fail
            if (not solved(status1)) and (not solved(status2)):
                if zeroScoreWhenBothFail:
                    scores['complete'] = (0,0)
                else:
                    scores['complete'] = (0,1)
            # both solvers complete
            elif (status1=='C') and (status2=='C'):
                scores['complete'] = (time2/(time1+time2), time1/(time1+time2))
            # both solvers give equal solution quality but without optimality proof
            else:
                assert (status1=='S') and (status2=='S')
                assert objs1[-1][1]==objs2[-1][1]
                lastTime1 = objs1[-1][0]
                lastTime2 = objs2[-1][0]
                scores['complete'] = (lastTime2/(lastTime1+lastTime2), lastTime1/(lastTime1+lastTime2))

        # incomplete scoring
        def better_optimisation_incomplete(s1,s2,o1,o2):
            if solved(s1) and not solved(s2):
                return True
            if solved(s1) and solved(s2) and len(o1)>0:
                assert len(o2)>0
                lastObj1 = o1[-1][1]
                lastObj2 = o2[-1][1]
                return has_better_objective(lastObj1, lastObj2, problemType)
            return False
        if better_optimisation_incomplete(status1, status2, objs1, objs2):
            scores['incomplete'] = (1,0)
        elif better_optimisation_incomplete(status2, status1, objs2, objs1):
            scores['incomplete'] = (0,1)
        else:
            # both solvers fail
            if (not solved(status1)) and (not solved(status2)):
                if zeroScoreWhenBothFail:
                    scores['incomplete'] = (0,0)
                else:
                    scores['incomplete'] = (0,1)
            # both solvers complete
            elif (status1=='C') and (status2=='C'):
                scores['incomplete'] = (time2/(time1+time2), time1/(time1+time2))
            # both solvers give equal solution quality
            else:
                assert solved(status1) and solved(status2)
                assert objs1[-1][1]==objs2[-1][1] # check if both solvers give the same solution quality
                lastTime1 = objs1[-1][0]
                lastTime2 = objs2[-1][0]
                scores['incomplete'] = (lastTime2/(lastTime1+lastTime2), lastTime1/(lastTime1+lastTime2))
    assert len(scores['complete'])==2
    assert len(scores['incomplete'])==2
    return scores


def run_comparator(info1, info2):
    """
    comparator for comparing results of two runs called by minizinc_solve
    return -1 if the first run is better, 0 if incomparable, and 1 otherwise
    note that problemType has to be added into either info1 or info2
    """
    assert conf.problemType in ['MIN','MAX','SAT']
    problemType = conf.problemType

    def solved(status):
        return status in ['S','C']

    def compare_time(t1, t2):
        if t1 < t2:
            return -1
        if t1 > t2:
            return 1
        return 0

    s1 = info1['status']
    s2 = info2['status']
    time1 = info1['time']
    time2 = info2['time']
    o1 = info1['extra']['objs']
    o2 = info2['extra']['objs']

    # decision problem
    if problemType=='SAT':
        def better_sat(s1,s2):
            if solved(s1) and not solved(s2):
                return True
            return False

        if better_sat(s1, s2):
            return -1
        if better_sat(s2, s1):
            return 1

        # instance is solved by both solvers
        if solved(s1) and solved(s2):
            return compare_time(time1,time2)
        # instance is unsolvable for both solvers
        else:
            assert (not solved(s1)) and (not solved(s2))
            return 0

    # optimisation problem
    else:
        def better_optimisation(s1,s2,o1,o2):
            if solved(s1) and not solved(s2):
                return True
            if (s1=='C') and (s2!='C'):
                return True
            if (s1==s2) and (s1=='S'):
                assert len(o1)>0 and len(o2)>0
                lastObj1 = o1[-1][1]
                lastObj2 = o2[-1][1]
                return has_better_objective(lastObj1, lastObj2, problemType)
            return False

        if better_optimisation(s1,s2,o1,o2):
            return -1
        if better_optimisation(s2,s1,o2,o1):
            return 1
        # both solvers fail
        if (not solved(s1)) and (not solved(s2)):
            return 0
        # both solvers complete
        elif (s1=='C') and (s2=='C'):
            return compare_time(time1, time2)
        # both solvers give equal solution quality but without optimality proof
        else:
            assert (s1=='S') and (s2=='S')
            assert o1[-1][1]==o2[-1][1]
            lastTime1 = o1[-1][0]
            lastTime2 = o2[-1][0]
            return compare_time(lastTime1, lastTime2)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run a minizinc problem')
    # general settings
    parser.add_argument('--modelFile', required=True, type=str, help='model file')
    parser.add_argument('--instFile', required=True, type=str, help='Instance file')
    parser.add_argument('--solver', required=True, type=str, help='solver to use')
    parser.add_argument('--solvCheck', required=True, type=str, help='list of solvers to use in a comma separated style: name1,name2,name3... Pass an empty string (\"\") to not check the solution')

    # read from command line args
    args = parser.parse_args()

    solvers = args.solvCheck.split(',')

    # run the "main"
    minizinc_solve(args.modelFile, args.instFile, args.solver, solvers_to_check=solvers)

