from utils import log, read_file, search_string, run_cmd, delete_file
import os
import sys
import json


def read_args(args):
    #### read arguments (following irace's wrapper input format) ###
    k = 1
    configurationId = int(args[k])
    k = k + 2  # skip second argument (<1>)
    seed = int(args[k])
    k = k + 2  # skip 4th argument (dummy instance name)
    params = args[k:]
    paramDict = {}  # generator parameter values suggested by irace
    for i in range(0, len(params), 2):
        paramDict[params[i][1:]] = params[i + 1]

    log(" ".join(args))

    return configurationId, seed, paramDict


def read_setting(settingFile):
    if os.path.isfile(settingFile) is False:
        print("ERROR: setting file " + settingFile + " is missing.")
        sys.exit(1)
    with open(settingFile) as f:
        setting = json.load(f)

    # split setting options into groups
    c = {"generalSettings": {}, "generatorSettings": {}, "evaluationSettings": {}}

    c["generalSettings"]["experimentType"] = setting["instanceSetting"]
    c["generalSettings"]["modelFile"] = setting["problemModel"]
    c["generalSettings"]["generatorFile"] = setting["generatorModel"]
    c["generalSettings"]["runDir"] = setting["runDir"]

    c["generatorSettings"]["genSRTimeLimit"] = setting["genSRTimeLimit"]
    c["generatorSettings"]["genSRFlags"] = setting["genSRFlags"]
    c["generatorSettings"]["genSolver"] = setting["genSolver"]
    c["generatorSettings"]["genSolverTimeLimit"] = setting["genSolverTimeLimit"]
    c["generatorSettings"]["genSolverFlags"] = setting["genSolverFlags"]

    c["evaluationSettings"]["nEvaluations"] = setting["nRunsPerInstance"]
    c["evaluationSettings"]["gradedTypes"] = setting["instanceValidTypes"]
    if setting["instanceSetting"] == "graded":
        c["evaluationSettings"]["solver"] = setting["solver"]
        print(setting)
        if setting["solver"] in ["yuck"]:
            c["evaluationSettings"]["solverType"] = "incomplete"
        else:
            c["evaluationSettings"]["solverType"] = "complete"
        c["evaluationSettings"]["minTime"] = setting["minSolverTime"]
        c["evaluationSettings"]["solverFlags"] = setting["solverFlags"]
        c["evaluationSettings"]["SRTimeLimit"] = setting["SRTimeLimit"]
        c["evaluationSettings"]["totalTimeLimit"] = setting["maxSolverTime"]
    else:
        c["evaluationSettings"][
            "scoringMethod"
        ] = "complete"  # NOTE: incomplete scoring method is also supported by the code
        baseSolverSettings = {
            "name": setting["baseSolver"],
            "solverMinTime": setting["minSolverTime"],
            "totalTimeLimit": setting["maxSolverTime"],
            "solverFlags": setting["baseSolverFlags"],
        }
        favouredSolverSettings = {
            "name": setting["favouredSolver"],
            "totalTimeLimit": setting["maxSolverTime"],
            "solverFlags": setting["favouredSolverFlags"],
        }

        c["evaluationSettings"]["baseSolver"] = baseSolverSettings
        c["evaluationSettings"]["favouredSolver"] = favouredSolverSettings

    return c