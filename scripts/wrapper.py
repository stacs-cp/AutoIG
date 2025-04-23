#!/usr/bin/env python

# wrapper for irace call to a run for generating instances from Conjure specification
# syntax: python wrapper.py <iraceConfigurationId> <1> <randomSeed> <dummyName> <configurationValues>
# output: the last stdout line is the score returned to irace

import os
import random
import time
import glob
import re
import json
from shutil import move
import datetime
from shutil import copyfile
import numpy as np
import copy
from functools import cmp_to_key
import pprint
import math
import conf
import sys

from wrapper_helpers import read_setting, read_args

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

from utils import log, read_file, search_string, run_cmd, delete_file
from essence_pipeline_utils import call_conjure_solve, encode_negative_table, get_essence_problem_type
from minizinc_utils import (
    minizinc_solve,
    calculate_minizinc_borda_scores,
    get_minizinc_problem_type,
    has_better_objective,
    run_comparator,
)
from generator import solve_generator
from convert import convert_essence_instance_to_mzn


# Define constants for scores
SCORE_UNWANTED_TYPE = 0
SCORE_TOO_EASY = 0
SCORE_TOO_DIFFICULT = 0
SCORE_INCORRECT_ANSWER = 0
SCORE_GRADED = -1

# Define constants for outputs
detailedOutputDir = "./detailed-output"

# for minizinc experiments only: solvers where -r doesn't work when being called via minizinc
deterministicSolvers = ["ortools"]


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
            essenceModelFile, eprimeModelFile, instFile, solver, SRTimeLimit, SRFlags, timeLimit, solverFlags, seed
        )

        # Append each iteration to the runs directory
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
):
    # TODO: we need to return a dictionary of results, as in evaluate_mzn_instance_discriminating
    # TODO: make all inputs of the function explicit, as in evaluate_mzn_instance_discriminating

    # Seeing what specifically is in this settings dictionary
    print("setting********", setting)
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

    essenceModelFile = "./problem.essence"
    eprimeModelFile = detailedOutputDir + "/problem.eprime"
    instance = os.path.basename(instFile).replace(".param", "")

    score = None
    results = {}

    def get_results():
        results["score"] = score
        results["status"] = status

    print("\n")
    log("Solving " + instFile + "...")

    print("testing")

    # solve the instance using each solver
    stop = False  # when to stop the evaluation early
    lsSolvingTime = {}  # solving time of each solver per random seed
    lsSolvingTime["favouredSolver"] = []
    lsSolvingTime["baseSolver"] = []
    for i in range(setting["nEvaluations"]):
        rndSeed = seed + i

        status = "ok"
        for solver in ["favouredSolver", "baseSolver"]:
            solverSetting = setting[solver]
            print(
                "\n\n---- With random seed "
                + str(i)
                + "th ("
                + str(rndSeed)
                + ") and solver "
                + solverSetting["name"]
                + " ("
                + solver
                + ")"
            )

            runStatus, SRTime, solverTime = call_conjure_solve(
                essenceModelFile, eprimeModelFile, instFile, solverSetting, rndSeed
            )
            localVars = locals()
            log(
                "\nRun results: solverType="
                + solver
                + ", solver="
                + solverSetting["name"]
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
                (setting["gradedTypes"] != "both")
                and (runStatus in ["sat", "unsat"])
                and (runStatus != setting["gradedTypes"])
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

    return score, get_results()


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
                if (info[solverType]["name"] in deterministicSolvers) or (
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
                score = SCORE_UNWANTED_TYPE
                status = "unwantedType"
                return score, get_results()

        # if the favoured solver cannot solve the instance on all runs, there's no need to run the base solver. We can just stop
        if (solverType == "favoured") and (solved is False):
            print("\nCannot be solved by favoured solver. Quitting...")
            score = SCORE_FAVOURED_TOO_DIFFICULT
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
        score = SCORE_BASE_TOO_EASY
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




def main():
    startTime = time.time()

    # parse arguments
    configurationId, seed, paramDict = read_args(sys.argv)

    # set random seed
    random.seed(seed)

    # read all setting
    setting = read_setting("./config.json")

    print(setting)

    # initialise run results
    score = status = None
    results = {"totalTime": 0, "genResults": {}, "instanceResults": {}}

    def print_results():
        assert (score is not None) and (status is not None)
        assert results["genResults"] != {}
        # if results['genResults']['status']=='sat':
        #    assert results['instanceResults']!={}
        totalWrapperTime = time.time() - startTime
        results["totalTime"] = totalWrapperTime
        results["status"] = status
        results["score"] = score
        print(results)
        print(str(score) + " " + str(np.round(totalWrapperTime, 2)))

    # solve the generator problem
    (
        genStatus,
        genSolFile,
        genMinionFile,
        genMinionSolString,
        genResults,
    ) = solve_generator(
        configurationId,
        paramDict,
        setting["generatorSettings"],
        seed,
        detailedOutputDir,
    )
    results["genResults"] = genResults

    # if no instance is generated, return immediately
    status = "gen" + genStatus
    if genStatus != "sat":
        print("No instance file generated. Exitting...")
        # determine the score
        if genStatus != "solverTimeOut":
            score = "Inf"  # if the generator configuration is unsat/SRTimeOut/SRMemOut/solverMemOut, return "Inf", so that irace will discard this configuration immediately
        else:
            score = 2  # if the generator configuration is unsolved because minion timeout, penalise it heavier than any other cases where the generator configuration is sat
        # print out score and exit
        print_results()
        return

    # if an instance is generated, move on and evaluate it
    instFile = (
        detailedOutputDir + "/inst-" + str(configurationId) + "-" + str(seed) + ".param"
    )
    move(genSolFile, instFile)

    experimentType = setting["generalSettings"]["experimentType"]
    assert experimentType in ["graded", "discriminating"], (
        "ERROR: invalid experimentType " + experimentType
    )

    modelType = os.path.basename(setting["generalSettings"]["modelFile"]).split(".")[-1]
    assert modelType in ["essence", "mzn"], (
        "ERROR: "
        + modelFile
        + ": model type not recognised (must be either .essence or .mzn)"
    )

    def get_unwanted_types():
        gradedTypes = (
            setting["evaluationSettings"]["gradedTypes"]
            .strip()
            .replace(" ", "")
            .replace("\t", "")
        )
        assert gradedTypes in ["all", "sat", "unsat", "sat,unsat", "unsat,sat"]
        if gradedTypes in ["all", "sat,unsat", "unsat,sat"]:
            return []
        if gradedTypes == "sat":
            return ["unsat"]
        return ["sat"]

    # evaluate the generated instance
    if modelType == "essence":
        
        
        # I dont think I need to do this, because.param are used in conjure
        # essenceInstFile = instFile.replace(".param",".dzn") 
        # # FIXME: this is a nearly direct take from the MZN implementation, 
        # I have double checked all the resulting entries in the settings and the minizinc inputs, 
        # but still not positive it will work
            # the line above replaces the filename sting
            # .param files are used in essence
            # .dzn files are used in minizinc 
        es = setting["evaluationSettings"]
        print("NEW SETTINGS DICT AGAIN: ", setting)
        if experimentType == "graded":
            oracleSolver = oracleSolverFlags = oracleSolverTimeLimit = None
            # only called for incomplete solvers, which aren't actually allowed yet
            if es["solverType"] == "incomplete":
                oracleSolver = "ortools"
                oracleSolverFlags = "-f"
                oracleSolverTimeLimit = 3600
            print("*** evaluate_essence_instance_graded DEBUG INFO ***")
            print(f"modelFile: problem.essence")
            print(f"instFile: {instFile}")
            print(f"unwantedTypes: {get_unwanted_types()}")
            print(f"nEvaluations: {es['nEvaluations']}")
            print(f"solver: {es['solver']}")
            print(f"solverFlags: {es['solverFlags']}")
            print(f"solverType: {es['solverType']}")
            print(f"minTime: {es['minTime']}")
            print(f"timeLimit: {es['totalTimeLimit']}")
            print(f"initSeed: {seed}")
            print(f"oracleSolver: {oracleSolver}")
            print(f"oracleSolverFlags: {oracleSolverFlags}")
            print(f"oracleSolverTimeLimit: {oracleSolverTimeLimit}")
            print("****************************************************")

            print("THE SR TIME LIMIT IS: ", es['SRTimeLimit'])

            score, instanceResults = evaluate_essence_instance_graded(
                modelFile="problem.essence",            # 
                instFile=instFile,                      # TODO: this is how the instfile was originaly passed, in think this is correct
                unwantedTypes=get_unwanted_types(),     # TODO: this is also different from essence, will have to be handled differently but is correct
                nEvaluations=es["nEvaluations"],        # correct
                solver=es["solver"],                    # correct
                solverFlags=es["solverFlags"],          # correct
                solverType=es["solverType"],            # correct
                minTime=es["minTime"],                  # correct
                timeLimit=es["totalTimeLimit"],         # correct
                SRTimeLimit=es["SRTimeLimit"],         # correct
                initSeed=seed,                          # correct
                oracleSolver=oracleSolver,              # oracle isnt implemented yet, so ignoring
                oracleSolverFlags=oracleSolverFlags,    #
                oracleSolverTimeLimit=oracleSolverTimeLimit,  #
            )
        else: 
            #TODO implement for discriminating
            score, instanceResults = evaluate_essence_instance_discriminating(
                modelFile="problem.essence",
                instFile=instFile,
                unwantedTypes=get_unwanted_types(),
                nEvaluations=es['nEvaluations'],
                baseSolver=
                baseSolverFlags=
                baseMinTime=
                favouredSolver=
                favouredSolverFlags=
                totalTimeLimit=
                initSeed=
                totalMemLimit=

            )
    else:
        # convert the generated instance into .dzn
        mznInstFile = instFile.replace(".param", ".dzn")
        convert_essence_instance_to_mzn("generator.essence", instFile, mznInstFile)

        # start the evaluation
        es = setting["evaluationSettings"]
        if es["nEvaluations"] == 1:
            seed = None
        if experimentType == "discriminating":
            assert (
                es["baseSolver"]["totalTimeLimit"]
                == es["favouredSolver"]["totalTimeLimit"]
            ), "ERROR: for mininzinc experiments, please set the same time limit for both base and favoured solvers"
            score, instanceResults = evaluate_mzn_instance_discriminating(
                modelFile="problem.mzn",
                instFile=mznInstFile,
                scoringMethod=es["scoringMethod"],
                unwantedTypes=get_unwanted_types(),
                nEvaluations=es["nEvaluations"],
                baseSolver=es["baseSolver"]["name"],
                baseSolverFlags=es["baseSolver"]["solverFlags"],
                baseMinTime=es["baseSolver"]["solverMinTime"],
                favouredSolver=es["favouredSolver"]["name"],
                favouredSolverFlags=es["favouredSolver"]["solverFlags"],
                totalTimeLimit=es["baseSolver"]["totalTimeLimit"],
                initSeed=seed,
            )

        else:
            oracleSolver = oracleSolverFlags = oracleSolverTimeLimit = None
            if es["solverType"] == "incomplete":
                oracleSolver = "ortools"
                oracleSolverFlags = "-f"
                oracleSolverTimeLimit = 3600
            score, instanceResults = evaluate_mzn_instance_graded(
                modelFile="problem.mzn",
                instFile=mznInstFile,
                unwantedTypes=get_unwanted_types(),
                nEvaluations=es["nEvaluations"],
                solver=es["solver"],
                solverFlags=es["solverFlags"],
                solverType=es["solverType"],
                minTime=es["minTime"],
                timeLimit=es["totalTimeLimit"],
                initSeed=seed,
                oracleSolver=oracleSolver,
                oracleSolverFlags=oracleSolverFlags,
                oracleSolverTimeLimit=oracleSolverTimeLimit,
            )

    results["instanceResults"] = instanceResults
    status = instanceResults["status"]

    # add the generated instance into generator's minion negative table, so that next time when we solve this generator instance again we don't re-generate the same instance
    encode_negative_table(genMinionFile, genMinionSolString)

    # print out score and exit
    print_results()

main()

# scoring for graded instances (single solver)
# - gen unsat/SRTimeOut/SRMemOut/solverMemOut: Inf
# - gen solverTimeout: 2
# - inst unwanted type or SR timeout/memout or solver crash: 1
# - solver timeout/memout: 0
# - otherwise, for each evaluation:
#   + too easy: -solverTime
#   + graded: nEvaluations * -solverMinTime
#   and sum them up for final score

# scoring for discriminating instances (two solvers)
# - gen unsat/SRTimeOut/SRMemOut/solverMemOut: Inf
# - gen solverTimeOut: 2
# - inst unwanted type or SR timeout/memout (either solver) or solver crash (either solver): 1
# - favoured solver timeout (any run) or base solver too easy (any run): 0
# - otherwise: max{-minRatio, -badSolver/goodSolver}
# - note: timelimit_badSolver = minRatio * timelimit_goodSolver
