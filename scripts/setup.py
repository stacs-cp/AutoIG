import datetime
import os
import sys
import argparse
from shutil import copyfile
from shutil import copy
from shutil import move
import json
import subprocess
import shlex
from collections import OrderedDict

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

import utils
from utils import log


def read_config(args):
    config = OrderedDict()

    generalSettings = [
        "runDir",
        "problemModel",
        "generatorModel",
        "seed",
        "maxEvaluations",
        "nCores",
    ]
    genSettings = [
        "genMaxInt",
        "genSRTimeLimit",
        "genSRFlags",
        "genSolver",
        "genSolverTimeLimit",
        "genSolverFlags",
    ]
    instSettings = [
        "instanceSetting",
        "instanceValidTypes",
        "minSolverTime",
        "maxSolverTime",
        "nRunsPerInstance",
    ]

    # read common settings for both graded/discriminating experiments
    for name in generalSettings + genSettings + instSettings:
        if getattr(args, name) is not None:
            config[name] = getattr(args, name)

    # genMaxInt is only used when generatorModel is automatically generated
    if "generatorModel" in config:
        del config["genMaxInt"]

    # convert all paths into absolute paths
    for name in ["runDir", "problemModel", "generatorModel"]:
        if name in config:
            config[name] = os.path.abspath(config[name])

    # read graded-specific settings
    if config["instanceSetting"] == "graded":
        for name in ["solver", "solverFlags"]:
            assert (
                getattr(args, name) is not None
            ), f"ERROR: --{name} is required for graded instance generation experiments."
            config[name] = getattr(args, name)

    # read discriminating-specific settings
    else:
        for name in [
            "favouredSolver",
            "favouredSolverFlags",
            "baseSolver",
            "baseSolverFlags",
        ]:
            assert (
                getattr(args, name) is not None
            ), f"ERROR: --{name} is required for discriminating instance generation experiments."
            config[name] = getattr(args, name)

    return config


def setup(config):
    log("Setting up the tuning: BEGIN")

    # create runDir
    if os.path.isdir(config["runDir"]):
        print("WARNING: directory " + config["runDir"] + " already exists")
    else:
        os.mkdir(config["runDir"])

    # save config file to runDir
    configFile = os.path.join(config["runDir"], "config.json")
    with open(configFile, "wt") as f:
        json.dump(config, f, indent=1)

    # get type of problem specification
    problemModelType = os.path.basename(config["problemModel"]).split(".")[-1]
    assert problemModelType in [
        "mzn",
        "essence",
    ], "ERROR: problemModel must end with either .essence or .mzn"

    # copy problem model to runDir
    problemModelFile = os.path.join(config["runDir"], "problem." + problemModelType)
    if os.path.abspath(problemModelFile) != os.path.abspath(config["problemModel"]):
        copyfile(config["problemModel"], problemModelFile)

    # remove .conjure-checksum file, otherwise error will be thrown if the script is run more than once
    try:
        os.remove(os.path.join(config["runDir"], ".conjure-checksum"))
    except OSError:
        pass

    # create a generator automatically from an Essence problem model via conjure
    # params.irace and repair.essence will be generated automatically by conjure
    generatorModelFile = os.path.join(config["runDir"], "generator.essence")
    repairModelFile = None
    if "generatorModel" not in config:
        assert (
            problemModelType == "essence"
        ), "ERROR: automated generator model is only supported if problemModel is written in Essence"

        # run "conjure parameter-generator"
        if config.generatorMaxInt <= 0:
            print("ERROR: generatorMaxInt must be positive")
            sys.exit(1)
        cmd = (
            "conjure parameter-generator "
            + problemModelFile
            + " --MAXINT="
            + str(config["generatorMaxInt"])
        )
        utils.log(cmd)
        utils.run_cmd(cmd)

        # rename generator spec
        move(
            problemModelFile.replace(".essence", "-instanceGenerator.essence"),
            generatorModelFile,
        )

        # rename irace param file
        move(
            problemModelFile.replace(".essence", "-instanceGenerator.essence.irace"),
            os.path.join(config["runDir"], "params.irace"),
        )

        # rename repair spec
        oldRepairModelFile = problemModelFile.replace(
            ".essence", "-instanceRepair.essence"
        )
        if os.path.isfile(oldRepairModelFile):
            repairModelFile = os.path.join(config["runDir"], "repair.essence")
            move(
                problemModelFile.replace(".essence", "-instanceRepair.essence"),
                repairModelFile,
            )

    # a generator model is already provided
    else:
        # copy the generator model to runDir
        if os.path.abspath(config["generatorModel"]) != os.path.abspath(generatorModelFile):
            copyfile(config["generatorModel"], generatorModelFile)

        # generate irace param files
        iraceParamFile = os.path.join(config["runDir"], "params.irace")
        cmd = (
            f"conjure autoig --generator-to-irace {generatorModelFile} {iraceParamFile}"
        )
        utils.log(cmd)
        utils.run_cmd(cmd)
        assert os.path.isfile(iraceParamFile), "ERROR: params.irace is missing"

        tmpPath = os.path.join(config["runDir"], "repair.essence")
        if os.path.isfile(tmpPath):
            repairModelFile = tmpPath

    # generate problem's eprime model
    if problemModelType == "essence":
        conjureTempDir = os.path.join(config["runDir"], "conjure-output")
        cmd = "conjure modelling -ac " + problemModelFile + " -o " + config["runDir"]
        utils.log(cmd)
        utils.run_cmd(cmd)
        move(
            os.path.join(config["runDir"], "model000001.eprime"),
            os.path.join(config["runDir"], "problem.eprime"),
        )

    # generate generator's eprime models
    cmd = "conjure modelling -ac " + generatorModelFile + " -o " + config["runDir"]
    utils.log(cmd)
    utils.run_cmd(cmd)
    move(
        os.path.join(config["runDir"], "model000001.eprime"),
        os.path.join(config["runDir"], "generator.eprime"),
    )

    # generate repair's eprime model
    if repairModelFile:
        cmd = "conjure modelling -ac " + repairModelFile + " -o " + config["runDir"]
        utils.log(cmd)
        utils.run_cmd(cmd)
        move(
            os.path.join(config["runDir"], "model000001.eprime"),
            os.path.join(config["runDir"], "repair.eprime"),
        )

    # create detailed-output folder and copy all .eprime models file into it
    detailedOutDir = os.path.join(config["runDir"], "detailed-output")
    if os.path.isdir(detailedOutDir) is False:
        os.mkdir(detailedOutDir)
        for fn in [
            "problem.essence",
            "problem.eprime",
            "generator.eprime",
            "repair.eprime",
        ]:
            if os.path.isfile(os.path.join(config["runDir"], fn)):
                copy(os.path.join(config["runDir"], fn), detailedOutDir)

    # copy other neccessary files
    for fn in ["instances", "run-irace.sh", "run.sh"]:
        copy(os.path.join(scriptDir, fn), config["runDir"])

    # update fields in run-irace.sh
    iraceFile = os.path.join(config["runDir"], "run-irace.sh")
    dictValues = {
        "seed": config["seed"],
        "nCores": config["nCores"],
        "maxExperiments": config["maxEvaluations"],
        "targetRunner": f"{scriptDir}/target-runner",
        "scenario": f"{scriptDir}/scenario.R",
    }
    with open(iraceFile, "rt") as f:
        lsLines = f.readlines()
    for field, value in dictValues.items():
        lsLines = [s.replace("<" + field + ">", str(value)) for s in lsLines]
    with open(iraceFile, "wt") as f:
        f.writelines(lsLines)

    log(f"All settings are saved in {configFile}")
    log("Setting up the tuning: COMPLETED\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Set up a tuning experiment for automated instance generation"
    )

    # general settings
    parser.add_argument(
        "--runDir",
        default="./",
        type=str,
        help="directory where the experiment will be run",
    )
    parser.add_argument(
        "--problemModel",
        required=True,
        type=str,
        help="path to a problem specification model in Essence/MiniZinc",
    )
    parser.add_argument(
        "--generatorModel",
        default=None,
        type=str,
        help="path to an instance generator model in Essence",
    )
    parser.add_argument("--seed", default=42, type=int, help="random seed")
    parser.add_argument(
        "--maxEvaluations",
        default=2000,
        type=int,
        help="maximum number of evaluations used by the tuning'",
    )
    parser.add_argument(
        "--nCores",
        default=1,
        type=int,
        help="how many processes running in parallel for the tuning",
    )

    # generator settings
    parser.add_argument(
        "--genMaxInt",
        default=50,
        type=int,
        help="(for automated generator only) maximum integer value, used for defining upper bounds of domains",
    )
    parser.add_argument(
        "--genSRTimeLimit",
        default=300,
        help="Savile Row time limit on each generator instance (in seconds)",
    )
    parser.add_argument(
        "--genSRFlags",
        default="-S0 -no-bound-vars",
        help="Savile Row extra flags for solving a generator instance",
    )
    parser.add_argument(
        "--genSolver",
        default="minion",
        choices=["minion"],
        help="solver used for solving each generator instance (only minion is supported at the moment)",
    )
    parser.add_argument(
        "--genSolverTimeLimit",
        default=300,
        help="time limit for solving each generator instance (in seconds)",
    )
    parser.add_argument(
        "--genSolverFlags",
        default="-varorder domoverwdeg -valorder random",
        help="extra flags for the generator solver",
    )

    # instance settings (for both graded and discriminating)
    parser.add_argument(
        "--instanceSetting",
        required=True,
        choices=["graded", "discriminating"],
        help="type of instance generation experiment (graded/discrminating)",
    )
    parser.add_argument(
        "--instanceValidTypes",
        default="all",
        choices=["sat", "unsat", "all"],
        help="type of instances being accepted (sat/unsat/all)",
    )
    parser.add_argument(
        "--minSolverTime",
        default=0,
        type=int,
        help="instances solved within less than minSolverTime seconds are considered trivial and will be discarded. For discriminating instance generation, this requirement is only applied to the base solver.",
    )
    parser.add_argument(
        "--maxSolverTime",
        required=True,
        type=int,
        help="time limit when solving an instance (in seconds)",
    )
    parser.add_argument(
        "--nRunsPerInstance", default=1, type=int, help="number of runs per instance"
    )

    # instance setting (for graded experiment only)
    parser.add_argument(
        "--solver",
        type=str,
        help="(graded instance generation only) solver used in the graded experiment",
    )
    parser.add_argument(
        "--solverFlags",
        type=str,
        default="",
        help="(graded instance generation only) extra flags for solver",
    )

    # instance setting (for discriminating experiment only)
    parser.add_argument(
        "--favouredSolver",
        type=str,
        help="(discriminating instance generation only) the favoured solver. We want to generate instances that are easy for this solver.",
    )
    parser.add_argument(
        "--favouredSolverFlags",
        type=str,
        default="",
        help="(discriminating instance generation only) extra flags for the favoured solver.",
    )
    parser.add_argument(
        "--baseSolver",
        type=str,
        help="(discriminating instance generation only) the base solver. We want to generate instances that are difficult for this solver.",
    )
    parser.add_argument(
        "--baseSolverFlags",
        type=str,
        default="",
        help="(discriminating instance generation only) extra flags for the base solver.",
    )

    # read all settings into one variable and check setting validity
    args = parser.parse_args()
    config = read_config(args)

    # set up tuning directory
    setup(config)


main()
