import os
from utils import log
from essence_pipeline_utils import call_conjure_solve, get_essence_problem_type

import conf # External file for holding static configurations, no need to redeclare here


def evaluate_essence_instance_graded(    
    modelFile: str, # Path to the Essence model file
    instFile: str, # Path to the instance parameter file
    unwantedTypes: list = [], # List of unwanted types
    nEvaluations: int = 1,  # Number of repeated solver runs
    solver: str = "ortools", #Name of the solver to use, default is ortools
    solverFlags: str = "-f", # Flags for the solver, fed into Conjure
    solverType: str = "complete", # The type of the provided solver, default is complete
    minTime: int = 10, # The minimum time threshold for the solver
    timeLimit: int = 1200, # The default time limit for each solver run
    initSeed: int = None, # The initial seed
    SRTimeLimit: int = 0, # The timelimit for SR
    SRFlags: str = "",  # Flags for SR

    # Currently no oracle implemented, left here in case it is done later on
    oracleSolver: str = None,
    oracleSolverFlags: str = "-f",
    oracleSolverTimeLimit: int = 3600,
    memLimit=8192, # Total memory limit for solver runs (currently unused)
):
    
    
    """
    evaluate an Essence instance with a single solver (goal: find graded instance for the given solver)
    """
    # same implementation used as in the existing Essence pipeline
    # using the new parameters passed in:
    essenceModelFile = "./" + modelFile # Model file has sting "problem.essence" passed in
    eprimeModelFile = conf.detailedOutputDir + "/problem.eprime"
    instance = os.path.basename(instFile).replace(".param", "")

    score = None
    results = {}
    status = "ok"

    # check validity of input: similar to how it was done for MZN implementation
    if len(unwantedTypes) > 0:
        for s in unwantedTypes:
            assert s in [
                "sat",
                "unsat",
            ], "ERROR: elements of unwantedTypes must be in {'sat','unsat'}"
    assert nEvaluations > 0
    assert solverType in [
        "complete",
        "incomplete",
    ], "ERROR: solver type must be either complete or incomplete"
    # Again, leaving so can be used in the future if the oracle is implemented
    if solverType == "incomplete":
        assert (
            oracleSolver != None
        ), "ERROR: for incomplete solver, an oracle solver must be used"
    assert (
        minTime < timeLimit
    ), "ERROR: min solving time must be less than total time limit"

    # Get the essence problem type using Conjure AST functionality
    problemType = get_essence_problem_type(modelFile)   
    conf.problemType = problemType

    # initialise results dictionaries
    results = {"main": {}, "oracle": {}}
    for st in ["main", "oracle"]:
        results[st]["runs"] = []
    score = status = None

    # Function to get results
    def get_results():
        assert (score is not None) and (
            status is not None
        ), "ERROR: score/status is missing"
        rs = {
            "instance": instFile,
            "status": status,
            "score": score,
            "results": results,
        }
        # print("\n",rs)
        return rs
    

 
    # Starting the actual Essence instance generation object
    print("\n")
    log("Solving " + instFile + "...")
    # run the main solver
    # These variables aren't currently used, left for future implementation
    instanceType = None
    optimalObj = None
    lsSolverTime = []   
    
    # Looping for each iteration of the nEvaluations parameter
    for i in range(nEvaluations):
        # Change seed each time
        if initSeed:
            seed = initSeed + i
        else:
            seed = None

        print(
            "\n\n----------- With seed " + str(i) + "th (" + str(seed) + ")"
        )

        # call conjure solve
        runStatus, SRTime, solverTime = call_conjure_solve(
            essenceModelFile, eprimeModelFile, instFile, solver, SRTimeLimit, SRFlags, timeLimit, solverFlags, seed
        )

        # Append each iteration to the runs directory
        results["main"]["runs"].append(
            {"seed": seed, "status": runStatus, "solverTime": solverTime,"SRTime": SRTime } # there is no extra attribute to print
        )

        # Minizinc had a check here for if the instance type was the same as the previous command
        # checked for inconsistencies but isn't possible here, no "EXTRA" field returned
        # there was a check here based on the optimal objective, but not possible

        # Checking if the result is an unwanted type
        if len(unwantedTypes) > 0 and runStatus and (runStatus in unwantedTypes):
            print("Unwanted instance type. Quitting...")
            score = conf.SCORE_UNWANTED_TYPE
            status = "unwantedType"
            return score, get_results()
        

    # Calculate median runtime
    results["main"]["runs"] = sorted(
        results["main"]["runs"], key=lambda run: run["solverTime"]
    )
    nRuns = len(results["main"]["runs"])
    medianRun = results["main"]["runs"][int(nRuns / 2)]


    # if the instance is too easy by the main solver, can just return now, no need to run the oracle
    if (medianRun["status"] == "sat") and (medianRun["solverTime"] < minTime):
        print("Instance too easy. Quitting...")
        score = conf.SCORE_TOO_EASY
        status = "tooEasy"  
        return score, get_results()
    
        # if the instance is unsolvable by the main solver, there's no need to run the oracle
    if medianRun["status"] not in ["sat"]:
        print("Instance not satisfiable or timeout occurred. Quitting...")
        score = conf.SCORE_TOO_DIFFICULT
        status = "tooDifficult"
        return score, get_results()

    status = "ok"
    score = conf.SCORE_GRADED
    return score, get_results()
