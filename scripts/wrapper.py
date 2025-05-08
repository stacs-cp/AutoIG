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

from conf import (
    detailedOutputDir,
)

from evaluators.essence_graded import evaluate_essence_instance_graded
from evaluators.essence_discriminating import evaluate_essence_instance_discriminating
from evaluators.mzn_graded import evaluate_mzn_instance_graded
from evaluators.mzn_discriminating import evaluate_mzn_instance_discriminating
# Imports 
import conf
scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

from utils import log, read_file, search_string, run_cmd, delete_file
from essence_pipeline_utils import encode_negative_table
from generator import solve_generator
from convert import convert_essence_instance_to_mzn


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

    # TODO can make this display more information if available
    modelType = os.path.basename(setting["generalSettings"]["modelFile"]).split(".")[-1]
    assert modelType in ["essence", "mzn"], (
        "ERROR: "
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
            print("************** printing es", es)
            score, instanceResults = evaluate_essence_instance_discriminating(
                modelFile="problem.essence",
                instFile=instFile,
                scoringMethod=es["scoringMethod"],
                unwantedTypes=get_unwanted_types(),
                nEvaluations=es['nEvaluations'],
                baseSolver=es["baseSolver"]["name"],
                baseSolverFlags=es["baseSolver"]["solverFlags"],
                baseMinTime=es["baseSolver"]["solverMinTime"],
                favouredSolver=es["favouredSolver"]["name"],
                favouredSolverFlags=es["favouredSolver"]["solverFlags"],
                # timeLimit=es["totalTimeLimit"],         # correct
                totalTimeLimit=es["baseSolver"]["totalTimeLimit"],
                initSeed=seed,
                gradedTypes=es["gradedTypes"],
                # SRTimeLimit=es["SRTimeLimit"],         # correct
                # SRFlags=es["SRTimeLimit"],         # correct


                # totalMemLimit=
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
    print("instance results *******", instanceResults)
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
