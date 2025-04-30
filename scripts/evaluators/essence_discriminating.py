import os, random, time
from utils import log
from essence_pipeline_utils import call_conjure_solve, get_essence_problem_type
import copy
import conf

def evaluate_essence_instance_discriminating(
    # instFile, 
    # seed, 
    # setting
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
    SRTimeLimit: int = 0,
    SRFlags: str = "",  # same default as povideed in make_conjure_solve command previously
    gradedTypes: str = "",
    # solverTimeLimit: int = 0,   #temporary replacement for totalTimeLimt

):
    
    print(" am getting to here*******************")
    # TODO: we need to return a dictionary of results, as in evaluate_mzn_instance_discriminating
    # TODO: make all inputs of the function explicit, as in evaluate_mzn_instance_discriminating

    # Seeing what specifically is in this settings dictionary
    # print("setting********", setting)
    """evaluate a generated instance based on discriminating power with two solvers ###
    " NOTE:
    " - this function can be improved using parallelisation, as there are various cases in the scoring where runs can be safely terminated before they finished. Things to consider
    "       + gnu-parallel for implementation
    "       + runsolver for safely terminating a solver run
    "
    " scoring scheme for discriminating solvers:
    " - gen unsat/SR memout/SR timeout: Inf
    " - gen solver timeout: 2
    " - inst unwanted type or SR timeout (either solver): 1 (ISSUE: with this new implementation, we can't recognise SR timeout, so we treat it as both solver timeout, i.e., score=0)
    " - favoured solver timeout (any run) or base solver too easy (any run): 0
    " - otherwise: max{-minRatio, -baseSolver/favouredSolver}
    " - note: if minRatio>0, ideally we should set timelimit_baseSolver = minRatio * timelimit_favouredSolver
    """


   # settings that stay hte same across runs
    essenceModelFile = "./problem.essence"
    eprimeModelFile = conf.detailedOutputDir + "/problem.eprime"
    instance = os.path.basename(instFile).replace(".param", "")


    """ taken directly from minizinc """
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

    """Nearly all above is directly taken from minizinc"""
 

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


    print("\n")
    log("Solving " + instFile + "...")

    correctedType = None
    
    # solve the instance using each solver
    stop = False  # when to stop the evaluation early
    lsSolvingTime = {}  # solving time of each solver per random seed
    lsSolvingTime["favouredSolver"] = []
    lsSolvingTime["baseSolver"] = []

    for solverType in ["favouredSolver", "baseSolver"]:
        solved = False

        if solver == favouredSolver:
            solverSetting = favouredSolverFlags
            current_solver  = favouredSolver

        else:
            solverSetting = baseSolverFlags
            current_solver  = baseSolver

        # solverSetting = str(solver) + "Flags"
        print("Solversetting: ", solverSetting)
        print("About to enter loop for nEvaluations")
        
        for i in range(nEvaluations):
            # Minizinc had this not be plus one
            rndSeed = initSeed + i

            # status = "ok"
            # solverSetting = {}
            # current_solver = None
                # print(
                #     "\n\n---- With random seed "
                #     + str(i)
                #     + "th ("
                #     + str(rndSeed)
                #     + ") and solver "
                #     + solverSetting["name"]
                #     + " ("
                #     + solver
                #     + ")"
                # )
            if i > 0:
                assert len(results[solverType]["runs"]) > 0
                flattenStatus = results[solverType]["runs"][0]["extra"]["flattenStatus"]
                if (info[solverType]["name"] in conf.deterministicSolvers) or (
                    flattenStatus != "ok"
                ):
                    r = copy.deepcopy(results[solverType]["runs"][0])
                    r["seed"] = rndSeed
                    results[solverType]["runs"].append(r)
                    continue


            print("reaching conjure solve point")
            runStatus, SRTime, solverTime = call_conjure_solve(
                essenceModelFile, eprimeModelFile, instFile, current_solver, SRTimeLimit, SRFlags, totalTimeLimit, solverSetting, rndSeed
            )
            localVars = locals()
  
            ## has none of these checks, because there is no extra

            ##TODO have to check which of htese is returned by hte SR pipeline again
            # Different because of the different results reutrned by SRpipeline
            if runStatus in ["sat", "nsat"]:
                if instanceType is None:
                    instanceType = status
                    assert instanceType in ["sat", "nsat"]
                    solved = True


                # for if it hasn't already been run in a previous nEvaluation 
                else:
                    if instanceType is None:
                        # if instanceType != status:
                        if correctedType is None:
                            # use a third solver, chuffed, to solve hte instance
                            c_runStatus, c_SRTime, c_solverTime = call_conjure_solve(
                                    essenceModelFile, 
                                    eprimeModelFile,
                                    instFile, 
                                    "chuffed", 
                                    SRTimeLimit, 
                                    SRFlags, 
                                    totalTimeLimit, 
                                    None, 
                                    rndSeed
                                )
                            assert c_runStatus in [
                                "sat",
                                "nsat"
                            ], "Error: Third solver (chuffed) also fails to prove sat or unsat"
                            correctedType = c_runStatus
                        if instanceType == correctedType:
                            solver = info[solverType]["name"]
                            print(
                                f"WARNING: incorrect results by {solver} on {instFile} with seed {seed}. Results returned: {extra['instanceType']}, while chuffed returns {correctedType}"
                            )
                            runStatus = "ERR"
                        if status == correctedType:
                            for st in results.keys():
                                for r in results[st]["runs"]:
                                    if r["extra"]["instanceType"] == instanceType:
                                        print(
                                            f"WARNING: incorrect results by {info[st]['name']} on {instFile} with seed {r['seed']}. Results returned: {r['extra']['instanceType']}, while chuffed returns {correctedType}"
                                        )
                                        r["status"] = "ERR"
                        instanceType = correctedType

            results[solverType]["runs"].append(
                {
                    "seed":rndSeed,
                    "status":runStatus,
                    "SRTime":SRTime,
                    "solverTime":solverTime,
                }
            )

            if (
                len(unwantedTypes) > 0
                and instanceType
                and (instanceType in unwantedTypes)
            ):
                print("Unwanted instance type. Quitting...")
                score = conf.SCORE_UNWANTED_TYPE
                status = "unwantedType"
                return score, get_results()
            

        if (solverTYpe == "favoured") and (solved is False):
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
    
    problemType = get_essence_problem_type(modelFile)


    # In minizinc pipeline here there was another OR-tools check, no need here, theres no objective function
    baseScores = []
    favouredScores = []
    # here other pipeline calculates "minizinc borda scores"
    # TODO not sure if im supposd to replicate that or what, but can try

            # lsSolvingTime[solver].append(solverTime)

            # ------------ update score
            # inst unwanted type: score=1
            if (
                (gradedTypes != "both")
                and (runStatus in ["sat", "unsat"])
                and (runStatus != gradedTypes)
            ):
                print("\nunwanted instance type. Quitting!...")
                score = 1
                stop = True
                status = "unwantedType"
                break
            # SR timeout or SR memout: score=1
            if runStatus in ["SRTimeOut", "SRMemOut"]:
                print(
                    "\nSR timeout/memout while translating the instance. Quitting!..."
                )
                score = 1
                stop = True
                status = runStatus
                break
            # solver crashes
            if runStatus == "solverCrash":
                print("\nsolver crashes. Quitting!...")
                score = 1
                stop = True
                status = runStatus
                break
            # favoured solver timeout (any run) or base solver too easy (any run): score=0
            if (solver == "favouredSolver") and (runStatus == "solverTimeOut"):
                print("\nfavoured solver timeout. Quitting!...")
                score = 0
                stop = True
                status = "favouredTimeOut"
                break
            if (solver == "baseSolver") and (
                solverTime < solverSetting["solverMinTime"]
            ):
                print("\ntoo easy run for base solver. Quitting!...")
                score = 0
                stop = True
                status = "baseTooEasy"
                break

        # evaluation is stopped as there's no need to test the rest
        if stop:
            break

    # if nothing is stop prematurely, calculate mean solving time & ratio, and update score
    ratio = 0
    if stop is False:
        meanSolverTime_favouredSolver = np.mean(lsSolvingTime["favouredSolver"])
        meanSolverTime_baseSolver = np.mean(lsSolvingTime["baseSolver"])
        ratio = meanSolverTime_baseSolver / meanSolverTime_favouredSolver
        # if minRatio is provided, use it
        if setting["minRatio"] != 0:
            score = max(-setting["minValue"], -ratio)
        else:  # otherwise, simply use the current ratio
            score = -ratio

        print("\n\nMean solving time: ")
        print(
            "\t- Favoured solver: "
            + str(np.round(meanSolverTime_favouredSolver, 2))
            + "s"
        )
        print("\t- Base solver: " + str(np.round(meanSolverTime_baseSolver, 2)) + "s")
        print("\t- Ratio: " + str(np.round(ratio, 2)))

    # print summary for later analysis
    favouredSolverTotalTime = baseSolverTotalTime = 0
    if len(lsSolvingTime["favouredSolver"]) > 0:
        favouredSolverTotalTime = sum(lsSolvingTime["favouredSolver"])
    if len(lsSolvingTime["baseSolver"]) > 0:
        baseSolverTotalTime = sum(lsSolvingTime["baseSolver"])
    s = (
        "\nInstance summary: instance="
        + instance
        + ", status="
        + status
        + ", favouredSolverTotalTime="
        + str(favouredSolverTotalTime)
        + ", baseSolverTotalTime="
        + str(baseSolverTotalTime)
        + ", ratio="
        + str(ratio)
    )
    print(s)

    print("returning score and get_results: ")
    print("score: ", score)
    print("results: ", get_results());
    return score, get_results()

