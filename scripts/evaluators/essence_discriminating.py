import os
from utils import log
from essence_pipeline_utils import call_conjure_solve, get_essence_problem_type, calculate_essence_borda_scores
import conf



def evaluate_essence_instance_discriminating(
    modelFile: str, # Path to the Essence model file 
    instFile: str, # Path to the instance parameter file
    scoringMethod: str = "complete", # Scoring method, complete by default
    unwantedTypes: list = [], # A list of unwanted types, empty by default
    nEvaluations: int = 1, # The number of iterations for each generator model, 1 by default
    baseSolver: str = "ortools", # Default baseSolver if none is provided
    baseSolverFlags: str = "-f", # Flags for the base solver, fed into Conjure
    baseMinTime: int = 0, # The minimum time threshold for the base solver
    favouredSolver: str = "yuck", # The default favoured solver, if none is provided
    favouredSolverFlags: str = "-f", # Flags for the favoured solver, fed into Conjure
    totalTimeLimit: int = 1200, # The default time limit for each solver run
    initSeed: int = None, # The initial seed
    totalMemLimit=8192, # Total memory limit for solver runs (currently unused)
    SRTimeLimit: int = 0, # The timelimit for SR
    SRFlags: str = "",  # Flags for SR
):
    
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


    # Set up file paths for Essence and EPrime files
    essenceModelFile = "./problem.essence"
    eprimeModelFile = conf.detailedOutputDir + "/problem.eprime"
    instance = os.path.basename(instFile).replace(".param", "")


    # Assertions to validate unwanted type and scoring method inputs
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

    # Initialize info and results dictionaries
    info = {
        "base": {"name": baseSolver, "flags": baseSolverFlags},
        "favoured": {"name": favouredSolver, "flags": favouredSolverFlags},
    }

    # Initialize results dictionary for each solver
    results = {"base": {}, "favoured": {}}
    for solverType in ["base", "favoured"]:
        results[solverType]["runs"] = []
    score = status = None
    instanceType = None

 
    # Create a function to return the results of the run
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
        return rs


    print("\n")
    log("Solving " + instFile + "...")

    correctedType = None
    
    # solve the instance using each solver
    stop = False  # when to stop the evaluation early
    lsSolvingTime = {}  # solving time of each solver per random seed
    lsSolvingTime["favoured"] = []
    lsSolvingTime["base"] = []

    for solverType in ["favoured", "base"]:
        solved = False

        if solverType == "favouredSolver":
            solverSetting = favouredSolverFlags
            current_solver  = favouredSolver

        else:
            solverSetting = baseSolverFlags
            current_solver  = baseSolver

        # solverSetting = str(solver) + "Flags"
        print("Solversetting: ", solverSetting)
        print("About to enter loop for nEvaluations")
        
        for i in range(nEvaluations):
            rndSeed = initSeed + i

            # Making the call to Conjure Solve
            runStatus, SRTime, solverTime = call_conjure_solve(
                essenceModelFile, eprimeModelFile, instFile, current_solver, SRTimeLimit, SRFlags, totalTimeLimit, solverSetting, rndSeed
            )
            localVars = locals()

            # Checking the produced run status
            if runStatus in ["sat", "nsat"]:
                if instanceType is None:
                    instanceType = runStatus
                    assert instanceType in ["sat", "nsat"]
                    solved = True


                # Condition if it hasn't already been run in a previous nEvaluation 
                else:
                    if instanceType is None:
                        # If a different result appears, verify with a third solver (chuffed)
                        if correctedType is None:
                            # use a third solver, chuffed, to solve the instance
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
                                f"WARNING: incorrect results by {solver} on {instFile} with seed {rndSeed}. Chuffed returns {correctedType}"
                            )
                            runStatus = "ERR"
                        if status == correctedType:
                            for st in results.keys():
                                for r in results[st]["runs"]:
                                    if r["status"] == instanceType:
                                        print(
                                            f"WARNING: incorrect results by {info[st]['name']} on {instFile} with seed {r['seed']}. Results returned: {r['extra']['instanceType']}, while chuffed returns {correctedType}"
                                        )
                                        r["status"] = "ERR"
                        instanceType = correctedType

            # Append run results
            results[solverType]["runs"].append(
                {
                    "seed":rndSeed,
                    "status":runStatus,
                    "SRTime":SRTime,
                    "solverTime":solverTime,
                }
            )

            # Early exit if instance type is unwanted
            if (
                len(unwantedTypes) > 0
                and instanceType
                and (instanceType in unwantedTypes)
            ):
                print("Unwanted instance type. Quitting...")
                score = conf.SCORE_UNWANTED_TYPE
                status = "unwantedType"
                return score, get_results()
            

        # For the case that the instance cannot be solved by the favoured solver
        if (solverType == "favoured") and (solved is False):
            print("\nCannot be solved by favoured solver. Quitting...")
            score = conf.SCORE_FAVOURED_TOO_DIFFICULT
            status = "favouredTooDifficult"
            return score, get_results()            

    # Check if the instance is too easy for the base solver
    baseAvgTime = sum([r["solverTime"] for r in results["base"]["runs"]]) / nEvaluations
    solvedByAllBaseRuns = True
    for r in results["base"]["runs"]:
        if r["status"] != "C":
            solvedByAllBaseRuns = False
            break
    print(solvedByAllBaseRuns)
    if solvedByAllBaseRuns and (baseAvgTime < baseMinTime):
        print("\nInstance is too easy for the base solver. Quitting...")
        score = conf.SCORE_BASE_TOO_EASY    # Setting the type appropriately
        status = "baseTooEasy"
        return score, get_results()
    
    # Getting the problem model type, using the AST produced by Conjure
    problemType = get_essence_problem_type(modelFile)


    # In minizinc pipeline here there were checks for objective value, is a TODO here for a later implementation
    baseScores = []
    favouredScores = []
    for i in range(nEvaluations):
        baseResults = results["base"]["runs"][i]
        favouredResults = results["favoured"]["runs"][i]

        # Calculating the borda scores based off only the solver time, no objective function implemented yet
        bordaScore = calculate_essence_borda_scores(
            baseResults["status"],
            favouredResults["status"],
            baseResults["solverTime"],
            favouredResults["solverTime"],
            problemType,
            True,
        )
        baseScores.append(bordaScore[0])
        favouredScores.append(bordaScore[1])

    # Adding up for the total scores
    baseSum = sum(baseScores)
    favouredSum = sum(favouredScores)


    # Aiming to maximise favouredSum / baseSum for these discriminating instances
    if favouredSum == 0:
        score = 0
    elif baseSum == 0:
        assert (
            favouredSum == nEvaluations
            # the best kind of instance possible, where base fails andfavoured succeeds
            
        )
        score = conf.SCORE_BEST
    else:
        score = (
            -favouredSum / baseSum
        )


    status = "ok"
    return score, get_results()
