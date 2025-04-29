import os, random, time
from utils import log
from essence_pipeline_utils import call_conjure_solve, get_essence_problem_type

import conf

def evaluate_essence_instance_discriminating(
    # instFile, 
    # seed, 
    # setting
    modelFile: str,
    instFile: str, 
    # scoringMethod: str = "complete",
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

    score = None
    results = {}


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

    print("testing")

    # solve the instance using each solver
    stop = False  # when to stop the evaluation early
    lsSolvingTime = {}  # solving time of each solver per random seed
    lsSolvingTime["favouredSolver"] = []
    lsSolvingTime["baseSolver"] = []
    for i in range(nEvaluations):
        rndSeed = initSeed + i

        status = "ok"
        solverSetting = {}
        current_solver = None
        for solver in ["favouredSolver", "baseSolver"]:

            if solver == favouredSolver:
                solverSetting = favouredSolverFlags
                current_solver  = favouredSolver

            else:
                solverSetting = baseSolverFlags
                current_solver  = baseSolver

            # solverSetting = str(solver) + "Flags"
            print("Solversetting: ", solverSetting)
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

            print("reaching conjure solve point")
            runStatus, SRTime, solverTime = call_conjure_solve(
                essenceModelFile, eprimeModelFile, instFile, current_solver, SRTimeLimit, SRFlags, totalTimeLimit, solverSetting, rndSeed
            )
            localVars = locals()
            log(
                "\nRun results: solverType="
                + solver
                + ", solver="
                + solverSetting
                + ", instance="
                + instance
                + ", runId="
                + str(i)
                + ", "
                + ", ".join(
                    [
                        s + "=" + str(localVars[s])
                        for s in ["runStatus", "SRTime", "solverTime"]
                    ]
                )
            )

            lsSolvingTime[solver].append(solverTime)

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

