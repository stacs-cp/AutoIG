from functools import cmp_to_key
from minizinc_utils import minizinc_solve, calculate_minizinc_borda_scores, get_minizinc_problem_type, has_better_objective

import copy
import conf


def evaluate_mzn_instance_discriminating(
    modelFile: str,
    instFile: str,
    scoringMethod: str = "complete",
    unwantedTypes: list = [],
    nEvaluations: int = 1,
    baseSolver: str = "ortools",
    baseSolverFlags: str = "-f",
    baseMinTime: int = 0,
    favouredSolver: str = "yuck",
    favouredSolverFlags: str = "-f",
    totalTimeLimit: int = 1200,
    initSeed: int = None,
    totalMemLimit=8192,
):
    """
    Evaluate a mzn instance under the solver-discriminating criteria
    """
    # Scores moved to be global variables so can be used elsewhere

    # check validity of input
    assert scoringMethod in ["complete", "incomplete"], (
        "ERROR: scoringMethod " + scoringMethod + " is not supported"
    )
    if len(unwantedTypes) > 0:
        for s in unwantedTypes:
            assert s in [
                "sat",
                "unsat",
            ], "ERROR: elements of unwantedTypes must be in {'sat','unsat'}"
    assert nEvaluations > 0

    # initialise info and results
    info = {
        "base": {"name": baseSolver, "flags": baseSolverFlags},
        "favoured": {"name": favouredSolver, "flags": favouredSolverFlags},
    }
    results = {"base": {}, "favoured": {}}
    for solverType in ["base", "favoured"]:
        results[solverType]["runs"] = []
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

    # run each solver on the instance and record results
    correctedType = None
    for solverType in ["favoured", "base"]:
        solved = False  # check if the instance is solved by this solver

        for i in range(nEvaluations):
            if initSeed:
                seed = initSeed + i
            else:
                seed = None

            # there are two cases where we only need to run a solver once and copy results to the remaining runs
            #   - case 1: the solver is deterministic
            #   - case 2: minizinc's flattening process fails
            if i > 0:
                assert len(results[solverType]["runs"]) > 0
                flattenStatus = results[solverType]["runs"][0]["extra"]["flattenStatus"]
                if (info[solverType]["name"] in conf.deterministicSolvers) or (
                    flattenStatus != "ok"
                ):
                    r = copy.deepcopy(results[solverType]["runs"][0])
                    r["seed"] = seed
                    results[solverType]["runs"].append(r)
                    continue

            print("\n")
            runStatus, runTotalTime, extra = minizinc_solve(
                modelFile,
                instFile,
                info[solverType]["name"],
                info[solverType]["flags"],
                seed,
                totalTimeLimit,
                totalMemLimit,
            )

            # for testing only
            # if solverType=='favoured':
            #    if extra['instanceType'] == 'sat':
            #        extra['instanceType']='unsat'

            # for testing only
            # if (solverType=='base') and (extra['instanceType']=='sat'):
            #    v = extra['objs'][-1]
            #    extra['objs'][-1] = (v[0], v[1]+1)

            # if the instance is solved by this run, update instanceType
            if runStatus in ["S", "C"]:
                assert extra["instanceType"] in ["sat", "unsat"]

                # if this is the first run where the instance is solved
                if instanceType is None:
                    instanceType = extra["instanceType"]
                    assert instanceType in ["sat", "unsat"]
                    solved = True
                    if len(extra["objs"]) > 0 and extra["objs"][-1]:
                        bestObj = extra["objs"][-1]

                # otherwise, check if two solvers or two runs of the same solvers return different answers
                else:
                    # if instance types (sat/unsat) are inconsistent
                    if instanceType != extra["instanceType"]:
                        if correctedType is None:
                            # use a third solver (chuffed) to solve the instance
                            c_runStatus, c_runTotalTime, c_extra = minizinc_solve(
                                modelFile,
                                instFile,
                                "chuffed",
                                "-f",
                                None,
                                totalTimeLimit,
                                totalMemLimit,
                            )
                            # TODO: what if chuffed fails to solve the instance?
                            assert c_extra["instanceType"] in [
                                "sat",
                                "unsat",
                            ], "ERROR: inconsistent results between solvers or between runs of the same solvers, and the third solver (chuffed) fails to determine which one is correct"
                            correctedType = c_extra["instanceType"]
                        # if the current run is the incorrected one, mark its status as ERR
                        if instanceType == correctedType:
                            solver = info[solverType]["name"]
                            print(
                                f"WARNING: incorrect results by {solver} on {instFile} with seed {seed}. Results returned: {extra['instanceType']}, while chuffed returns {correctedType}"
                            )
                            runStatus = "ERR"
                        # if the previous runs were the incorrected ones, mark their statuses as ERR
                        if extra["instanceType"] == correctedType:
                            for st in results.keys():
                                for r in results[st]["runs"]:
                                    if r["extra"]["instanceType"] == instanceType:
                                        print(
                                            f"WARNING: incorrect results by {info[st]['name']} on {instFile} with seed {r['seed']}. Results returned: {r['extra']['instanceType']}, while chuffed returns {correctedType}"
                                        )
                                        r["status"] = "ERR"
                        # assign the correct type
                        instanceType = correctedType

            results[solverType]["runs"].append(
                {
                    "seed": seed,
                    "status": runStatus,
                    "time": runTotalTime,
                    "extra": extra,
                }
            )

            # if the instance is of an unwanted type, we stop immediately
            if (
                len(unwantedTypes) > 0
                and instanceType
                and (instanceType in unwantedTypes)
            ):
                print("Unwanted instance type. Quitting...")
                score = conf.SCORE_UNWANTED_TYPE
                status = "unwantedType"
                return score, get_results()

        # if the favoured solver cannot solve the instance on all runs, there's no need to run the base solver. We can just stop
        if (solverType == "favoured") and (solved is False):
            print("\nCannot be solved by favoured solver. Quitting...")
            score = conf.SCORE_FAVOURED_TOO_DIFFICULT
            status = "favouredTooDifficult"
            return score, get_results()

    # check if the instance is too easy for the base solver
    baseAvgTime = sum([r["time"] for r in results["base"]["runs"]]) / nEvaluations
    solvedByAllBaseRuns = True
    for r in results["base"]["runs"]:
        if r["status"] != "C":
            solvedByAllBaseRuns = False
            break
    print(solvedByAllBaseRuns)
    if solvedByAllBaseRuns and (baseAvgTime < baseMinTime):
        print("\nInstance is too easy for the base solver. Quitting...")
        score = conf.SCORE_BASE_TOO_EASY
        status = "baseTooEasy"
        return score, get_results()

    problemType = get_minizinc_problem_type(modelFile)

    # if one of the two solvers is ortools and the instance is solved to optimality by ortools, use it to check correctness of the other solver in term of objective values before calculating borda score
    if instanceType == "sat":
        correctResults = toCheckResults = None
        toCheckSolver = None
        if info["base"]["name"] == "ortools":
            correctResults = results["base"]["runs"]
            toCheckResults = results["favoured"]["runs"]
            toCheckSolver = info["favoured"]["name"]
        elif info["favoured"]["name"] == "ortools":
            correctResults = results["favoured"]["runs"]
            toCheckResults = results["base"]["runs"]
            toCheckSolver = info["base"]["name"]
        if correctResults:
            optimal = None
            for r in correctResults:
                if r["status"] == "C":
                    optimal = r["extra"]["objs"][-1][1]
                    break
            if optimal:
                for r in toCheckResults:
                    if r["status"] in ["S", "C"]:
                        assert len(r["extra"]["objs"]) > 0
                        if has_better_objective(
                            r["extra"]["objs"][-1][1], optimal, problemType
                        ):
                            print(
                                f"WARNING: incorrect objective value by {toCheckSolver} on {instFile}. Best objective returned: {r['extra']['objs'][-1][1]}, while ortools returns {optimal}"
                            )
                            r["status"] = "ERR"

    # calculate minizinc score of each solver per run
    baseScores = []
    favouredScores = []
    print("\nBorda score for base and favoured solvers: ")
    for i in range(nEvaluations):
        baseResults = results["base"]["runs"][i]
        favouredResults = results["favoured"]["runs"][i]

        bordaScores = calculate_minizinc_borda_scores(
            baseResults["status"],
            favouredResults["status"],
            baseResults["time"],
            favouredResults["time"],
            problemType,
            baseResults["extra"]["objs"],
            favouredResults["extra"]["objs"],
            True,
        )
        print("bordascores****")
        print(bordaScores)
        sc = bordaScores[scoringMethod]
        baseScores.append(sc[0])
        favouredScores.append(sc[1])

    # summarise over all runs
    baseSum = sum(baseScores)
    favouredSum = sum(favouredScores)

    # we want to maximise favouredSum / baseSum
    if favouredSum == 0:
        score = 0
    elif baseSum == 0:
        assert (
            favouredSum == nEvaluations
        )  # the best type of instance we can achieve, where the base solver fails and the favoured solver succeeds
        score = -99999
    else:
        score = (
            -favouredSum / baseSum
        )  # when both solvers succeeds at solving the instance, we maximise the ratio of their scores

    status = "ok"
    return score, get_results()

