
def evaluate_essence_instance_graded(    
    modelFile: str, # present for MZN
    instFile: str, # present for mzn 
    unwantedTypes: list = [], # present for mzn
    nEvaluations: int = 1,  # present for MZN, 
    solver: str = "ortools", #present for mzn 
    solverFlags: str = "-f", # present for mzn 
    solverType: str = "complete", # present for mzn
    minTime: int = 10, # present for mzn 
    timeLimit: int = 1200, # present for mzn 
    initSeed: int = None, # present for mzn 
    SRTimeLimit: int = 0, # same default as provided in make_conjure_solve_command previously 
    SRFlags: str = "",  # same default as povideed in make_conjure_solve command previously
    solverTimeLimit: int = 0, # same default as provided in the make_conjure_solve command previously
    oracleSolver: str = None,
    oracleSolverFlags: str = "-f",
    oracleSolverTimeLimit: int = 3600,
    memLimit=8192,
):
    
    
    """
    evaluate an Essence instance with a single solver (goal: find graded instance for the given solver)
    """
    # same implementation used as in the existing Essence pipeline
    # using the new parameters passed in:
    essenceModelFile = "./" + modelFile # Model file has sting "problem.essence" passed in
    eprimeModelFile = detailedOutputDir + "/problem.eprime"
    instance = os.path.basename(instFile).replace(".param", "")

    # got rid of some usage of existing parameters, such as solver 

    score = None
    results = {}
    status = "ok"

    # check validity of input: identical to how it was done for MZN implementation
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
    if solverType == "incomplete":
        assert (
            oracleSolver != None
        ), "ERROR: for incomplete solver, an oracle solver must be used"
    assert (
        minTime < timeLimit
    ), "ERROR: min solving time must be less than total time limit"

    # TODO may need to change implementation of get_essence_problem_type
    problemType = get_essence_problem_type(modelFile)   
    conf.problemType = problemType

    # initialise results
    results = {"main": {}, "oracle": {}}
    for st in ["main", "oracle"]:
        results[st]["runs"] = []
    score = status = None

    # NOTE: updated get results from the minizinc pipeline
    # concerning because existing essence pipeline had two simultaneous versions of the function
    # was the same implementation as previously, should be fine
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
    
    """ 
    THIS IS WHERE THE ORACLE SHOULD BE HANDLED, EVERYTHING BEFOREHAND WAS JUST PARAMETER HANDLING
    """

    """ 
    THIS IS WHERE THE ACTUAL ESSENCE INSTANCE GENERATION STARTS
    """

    print("\n")
    log("Solving " + instFile + "...")
    # run the main solver
    instanceType = None
    optimalObj = None

    lsSolverTime = []   # FIXME: NOT SURE IF THIS SHOULD BE HERE, IS LEFTOVER FROM OLD ESSENCE IMPLEMENTATION 
    for i in range(nEvaluations):
        # FIXME: be careful about the way seed was handled, used to be rndseed
        if initSeed:
            seed = initSeed + i
        else:
            seed = None

        print(
            "\n\n----------- With seed " + str(i) + "th (" + str(seed) + ")"
        )

        #TODO did same implementatino for call_conjure_solve but need to check
        # this has both essenceModelFile, and eprimeModelFile, rather than just modelFile like minizinc
        # there is also two time limits, theres SRTimeLimit and solverTimeLimit
        runStatus, SRTime, solverTime = call_conjure_solve(
            essenceModelFile, eprimeModelFile, instFile, solver, SRTimeLimit, SRFlags, solverTimeLimit, solverFlags, seed
        )

        results["main"]["runs"].append(
            {"seed": seed, "status": runStatus, "solverTime": solverTime,"SRTime": SRTime } # there is no extra attribute to print
        )

        # Minizinc had a check here for if the instance type was the same as the previous command
        # checked for inconsistencies but isn't possible here, no "EXTRA" field returned
            
        # there was a check here based on the optimal objective, but not possible

        # there was a check for instance of an wanted type
        # doing this because runStatus returns sat or nsat
        if len(unwantedTypes) > 0 and runStatus and (runStatus in unwantedTypes):
            print("Unwanted instance type. Quitting...")
            score = SCORE_UNWANTED_TYPE
            status = "unwantedType"
            # TODO: in this context, we don't really need to run the oracle to check correctness of instance type, since return scores for unwanted type and incorrect results are the same. But if we decide to have the two scores being different, we may need to use the oracle here
            return score, get_results()
        
    # cant do this because don't have objective function
    # function to get the median run, and uses it to determine weather the instance is too easy 
    # I just took the median of the times used to solve it
    # just trying to take the mean based on solvertime alone
    results["main"]["runs"] = sorted(
        results["main"]["runs"], key=lambda run: run["solverTime"]
    )
    nRuns = len(results["main"]["runs"])
    medianRun = results["main"]["runs"][int(nRuns / 2)]


    # if the instance is too easy by the main solver, can just return now, no need to run the oracle
    if (medianRun["status"] == "sat") and (medianRun["solverTime"] < minTime):
        print("Instance too easy. Quitting...")
        score = SCORE_TOO_EASY
        status = "tooEasy"  #TODO maybe change based on how I implement the returns of this function
        return score, get_results()
    
        # if the instance is unsolvable by the main solver, there's no need to run the oracle
    if medianRun["status"] not in ["sat"]:
        print("Instance not satisfiable or timeout occurred. Quitting...")
        score = SCORE_TOO_DIFFICULT
        status = "tooDifficult"
        return score, get_results()

    status = "ok"
    score = SCORE_GRADED
    return score, get_results()
