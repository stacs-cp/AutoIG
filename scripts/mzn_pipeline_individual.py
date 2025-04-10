def evaluate_mzn_instance_graded(
    modelFile: str,
    instFile: str,
    unwantedTypes: list = [],
    nEvaluations: int = 1,
    solver: str = "ortools",
    solverFlags: str = "-f",
    solverType: str = "complete",
    minTime: int = 10,
    timeLimit: int = 1200,
    initSeed: int = None,
    oracleSolver: str = None,
    oracleSolverFlags: str = "-f",
    oracleSolverTimeLimit: int = 3600,
    memLimit=8192,
):
    """
    Evaluate a mzn instance under the gradedness criteria
    """
    # define constants for scores
    SCORE_UNWANTED_TYPE = 0
    SCORE_TOO_EASY = 0
    SCORE_TOO_DIFFICULT = 0
    SCORE_INCORRECT_ANSWER = 0
    SCORE_GRADED = -1

    # check validity of input
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

    # this is used by minizinc_utils.run_comparator
    problemType = get_minizinc_problem_type(modelFile)
    conf.problemType = problemType

    # initialise results
    results = {"main": {}, "oracle": {}}
    for st in ["main", "oracle"]:
        results[st]["runs"] = []
    score = status = None
    instanceType = None

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

    # if it's a deterministic solver, we only need to run it once
    # if (nEvaluations>1) and (solver in deterministicSolvers):
    #    nEvaluations = 1
    #    print(f"{solver} is a deterministic solver via minizinc, so we only need to run it once.")

    # TODO: if main solver is incomplete and we don't want unsat instances, it's better to run the oracle with a small amount of time to check for satisfiability first
    if (solverType == "incomplete") and ("unsat" in unwantedTypes):
        smallTimeLimit = 120
        oracleRunStatus, oracleRunTotalTime, oracleExtra = minizinc_solve(
            modelFile,
            instFile,
            oracleSolver,
            oracleSolverFlags,
            seed,
            smallTimeLimit,
            memLimit,
        )
        if oracleExtra["instanceType"] == "unsat":
            print("Unwanted instance type (checked by oracle). Quitting...")
            score = SCORE_UNWANTED_TYPE
            status = "unwantedType"
            # TODO: in this context, we don't really need to run the oracle to check correctness of instance type, since return scores for unwanted type and incorrect results are the same. But if we decide to have the two scores being different, we may need to use the oracle here
            return score, get_results()

    # run the main solver
    instanceType = None
    optimalObj = None
    for i in range(nEvaluations):
        if initSeed:
            seed = initSeed + i
        else:
            seed = None

        print("\n")
        runStatus, runTotalTime, extra = minizinc_solve(
            modelFile, instFile, solver, solverFlags, seed, timeLimit, memLimit
        )
        results["main"]["runs"].append(
            {"seed": seed, "status": runStatus, "time": runTotalTime, "extra": extra}
        )

        # just for testing
        # extra['instanceType']='unsat'

        # update instance type & check for inconsistency
        if runStatus in ["S", "C"]:
            if instanceType is None:
                instanceType = extra["instanceType"]
            elif (
                instanceType != extra["instanceType"]
            ):  # inconsistent results between runs, return immediately
                print("Inconsistent instance type between runs. Quitting...")
                score = SCORE_INCORRECT_ANSWER
                status = "inconsistentInstanceTypes"
                return score, get_results()

        # update optimal objective & check for inconsistency
        if (runStatus == "C") and (instanceType == "sat"):
            if optimalObj is None:
                assert len(extra["objs"]) > 0
                optimalObj = extra["objs"][-1][1]
            elif optimalObj != extra["objs"][-1][1]:
                print("Inconsistent optimal objective value between runs. Quitting...")
                score = SCORE_INCORRECT_ANSWER
                status = "inconsistentOptimalValues"
                return score, get_results()

        # if the instance is of an unwanted type, we stop immediately
        if len(unwantedTypes) > 0 and instanceType and (instanceType in unwantedTypes):
            print("Unwanted instance type. Quitting...")
            score = SCORE_UNWANTED_TYPE
            status = "unwantedType"
            # TODO: in this context, we don't really need to run the oracle to check correctness of instance type, since return scores for unwanted type and incorrect results are the same. But if we decide to have the two scores being different, we may need to use the oracle here
            return score, get_results()

    # get the median run
    results["main"]["runs"] = sorted(
        results["main"]["runs"], key=cmp_to_key(run_comparator)
    )
    nRuns = len(results["main"]["runs"])
    medianRun = results["main"]["runs"][int(nRuns / 2)]
    # pprint.pprint(results['main']['runs'])

    # if the instance is too easy by the main solver, there's no need to run the oracle
    if (medianRun["status"] == "C") and (medianRun["time"] < minTime):
        print("Instance too easy. Quitting...")
        score = SCORE_TOO_EASY
        status = "tooEasy"
        return score, get_results()

    # if the instance is unsolvable by the main solver, there's no need to run the oracle
    if medianRun["status"] not in ["S", "C"]:
        print("Instance too difficult. Quitting...")
        score = SCORE_TOO_DIFFICULT
        status = "tooDifficult"
        return score, get_results()

    if oracleSolver:
        # run the oracle
        # TODO: depending on results of the main solver, we do not necessarily run the oracle until the timelimit, e.g., if the main solver returns unsat, the oracle can stop as soon as it can find a (correct) solution. That might help to save lots of computation time.
        print("\nRunning the oracle")
        oracleRunStatus, oracleRunTotalTime, oracleExtra = minizinc_solve(
            modelFile,
            instFile,
            oracleSolver,
            oracleSolverFlags,
            seed,
            oracleSolverTimeLimit,
            memLimit,
        )
        results["oracle"]["runs"].append(
            {
                "status": oracleRunStatus,
                "time": oracleRunTotalTime,
                "extra": oracleExtra,
            }
        )

        # for testing only
        # v = oracleExtra['objs'][-1]
        # oracleExtra['objs'][-1] = (v[0], v[1]-1)

        if oracleRunStatus != "C":
            print("Instance cannot be solved by the oracle. Quitting...")
            score = SCORE_TOO_DIFFICULT
            status = "tooDifficultOracle"
            return score, get_results()

        # check correctness using the oracle
        for r in results["main"]["runs"]:
            # instance type
            # print(r)
            if (r["status"] in ["S", "C"]) and (
                r["extra"]["instanceType"] != oracleExtra["instanceType"]
            ):
                print("Incorrect results (checked by oracle). Quitting...")
                score = SCORE_INCORRECT_ANSWER
                status = "incorrectInstanceType"
                return score, get_results()
            # objective value
            if (r["status"] in ["S", "C"]) and (oracleExtra["instanceType"] == "sat"):
                assert len(r["extra"]["objs"]) > 0
                optimal = oracleExtra["objs"][-1][1]
                for o in r["extra"]["objs"]:
                    if has_better_objective(o[1], optimal, problemType):
                        print("Incorrect results (checked by oracle). Quitting...")
                        score = SCORE_INCORRECT_ANSWER
                        status = "incorrectObjectiveValue"
                        return score, get_results()
                if (r["status"] == "C") and (r["extra"]["objs"][-1][1] != optimal):
                    print("Incorrect results (checked by oracle). Quitting...")
                    score = SCORE_INCORRECT_ANSWER
                    status = "incorrectOptimalValue"
                    return score, get_results()

        # for incomplete solver, use oracle to determine status
        if (solverType == "incomplete") and (oracleExtra["instanceType"] == "sat"):
            assert medianRun["status"] in ["S", "C"]
            optimal = oracleExtra["objs"][-1][1]
            o = medianRun["extra"]["objs"][-1][1]
            assert has_better_objective(o, optimal, problemType) is False
            if o != optimal:
                print("Instance too difficult. Quitting...")
                score = SCORE_TOO_DIFFICULT
                status = "tooDifficult"
                return score, get_results()
            else:
                lastTime = medianRun["extra"]["objs"][-1][0]
                # if the main solver is incomplete and the optimal value is reached within in less than minTime seconds, consider the instance as too easy
                if lastTime < minTime:
                    print("Instance too easy. Quitting...")
                    score = SCORE_TOO_EASY
                    status = "tooEasy"
                    return score, get_results()

    status = "ok"
    score = SCORE_GRADED
    return score, get_results()