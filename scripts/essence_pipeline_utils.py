import os
import sys
import time
import glob

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

from utils import log, read_file, search_string, run_cmd, delete_file

solverInfo = {}
solverInfo["cplex"] = {
    "timelimitUnit": "ms",
    "timelimitPrefix": "--time-limit ",
    "randomSeedPrefix": "via text file",
}
solverInfo["chuffed"] = {
    "timelimitUnit": "ms",
    "timelimitPrefix": "-t ",
    "randomSeedPrefix": "--rnd-seed ",
}
solverInfo["minion"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-timelimit ",
    "randomSeedPrefix": "-randomseed ",
}
solverInfo["gecode"] = {
    "timelimitUnit": "ms",
    "timelimitPrefix": "-time ",
    "randomSeedPrefix": "-r ",
}
solverInfo["glucose"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-cpu-lim=",
    "randomSeedPrefix": "-rnd-seed=",
}
solverInfo["glucose-syrup"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-cpu-lim=",
    "randomSeedPrefix": "-rnd-seed=",
}
solverInfo["lingeling"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-T ",
    "randomSeedPrefix": "--seed ",
}
solverInfo["cadical"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-t ",
    "randomSeedPrefix": "--seed=",
}
solverInfo["open-wbo"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-cpu-lim=",
    "randomSeedPrefix": "-rnd-seed=",
}
solverInfo["boolector"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "--time=",
    "randomSeedPrefix": "--seed=",
}
solverInfo["kissat"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "--time=",
    "randomSeedPrefix": "--seed=",
}


def conjure_translate_parameter(eprimeModelFile, paramFile, eprimeParamFile):
    cmd = (
        "conjure translate-parameter "
        + "--eprime="
        + eprimeModelFile
        + " --essence-param="
        + paramFile
        + " --eprime-param="
        + eprimeParamFile
    )
    log(cmd)
    cmdOutput, returnCode = run_cmd(cmd)

    if returnCode != 0:
        raise Exception(cmdOutput)


def savilerow_translate(
    auxFile, eprimeModelFile, eprimeParamFile, minionFile, timelimit, flags
):
    cmd = (
        "savilerow "
        + eprimeModelFile
        + " "
        + eprimeParamFile
        + " -out-aux "
        + auxFile
        + " -out-minion "
        + minionFile
        + " -save-symbols "
        + "-timelimit "
        + str(timelimit)
        + " "
        + flags
    )
    log(cmd)
    
    start = time.time()
    cmdOutput, returnCode = run_cmd(cmd)
    SRTime = time.time() - start
    
    status = "SRok"
    # if returnCode !=0, check if it is because SR is out of memory or timeout
    if (
        ("GC overhead limit exceeded" in cmdOutput)
        or ("OutOfMemoryError" in cmdOutput)
        or ("insufficient memory" in cmdOutput)
    ):
        status = "SRMemOut"
    elif "Savile Row timed out" in cmdOutput:
        status = "SRTimeOut"
    # if returnCode != 0 and its not due to a timeout or memory issue raise exception to highlight issue
    elif returnCode != 0:
        raise Exception(cmdOutput)

    return status, SRTime


def savilerow_parse_solution(eprimeModelFile, minionSolFile, auxFile, eprimeSolFile):
    # command syntax: savilerow generator.eprime -mode ReadSolution -out-aux output.aux -out-solution sol.test -minion-sol-file test.txt
    cmd = (
        "savilerow "
        + eprimeModelFile
        + " -mode ReadSolution -out-aux "
        + auxFile
        + " -out-solution "
        + eprimeSolFile
        + " -minion-sol-file "
        + minionSolFile
    )
    cmdOutput, returnCode = run_cmd(cmd)

    log(cmd)
    if returnCode != 0:
        raise Exception(cmdOutput)


def conjure_translate_solution(
    eprimeModelFile, paramFile, eprimeSolFile, essenceSolFile
):
    cmd = (
        "conjure translate-solution --eprime="
        + eprimeModelFile
        + " --essence-param="
        + paramFile
        + " --eprime-solution="
        + eprimeSolFile
        + " --essence-solution "
        + essenceSolFile
    )
    log(cmd)

    cmdOutput, returnCode = run_cmd(cmd)

    if returnCode != 0:
        raise Exception(cmdOutput)


def run_minion(minionFile, minionSolFile, seed, timelimit, flags):
    cmd = (
        "minion "
        + minionFile
        + " -solsout "
        + minionSolFile
        + " -randomseed "
        + str(seed)
        + " -timelimit "
        + str(timelimit)
        + " "
        + flags
    )
    log(cmd)

    start = time.time()
    cmdOutput, returnCode = run_cmd(cmd)
    runTime = time.time() - start

    # check if minion is timeout or memout
    status = None
    if "Time out." in cmdOutput:
        status = "solverTimeOut"
    elif (
        ("Error: maximum memory exceeded" in cmdOutput)
        or ("Out of memory" in cmdOutput)
        or ("Memory exhausted!" in cmdOutput)
    ):
        status = "solverMemOut"
    elif returnCode != 0:
        raise Exception(cmdOutput)
    else:
        if "Solutions Found: 0" in cmdOutput:
            status = "unsat"
        else:
            status = "sat"

    return status, runTime


def read_minion_variables(minionFileSections):
    search_section = minionFileSections["SEARCH"]
    for line in search_section:
        if "PRINT" in line:
            variables = line.split("PRINT")[1]
            variables = variables.replace("[", "").replace("]", "")
            return variables

    raise Exception("Cant find minion ordered variables section")


def parse_minion_file(minionFile):
    minionFileSections = {}
    lines = []
    file = open(minionFile, "r")
    current_section = None
    for line in file:
        if "**" in line:
            if current_section is not None:
                if (
                    line.strip()[0] != "*"
                ):  # in case the section header is on the same line with the last line of the previous section's content
                    s = line[: line.find("*")]
                    lines.append(s)
                if current_section in minionFileSections:
                    minionFileSections[current_section].extend(lines)
                else:
                    minionFileSections[current_section] = lines
            current_section = line.replace("*", "").strip()
            lines = []
            continue

        lines.append(line)

    file.close()
    return minionFileSections


def parse_minion_solution(minionSolFile):
    with open(minionSolFile) as solFile:
        return solFile.read().strip()


def write_out_modified_minion_file(minionFile, minionFileSections):
    file = open(minionFile, "w")
    minionSectionKeys = ["VARIABLES", "SEARCH", "TUPLELIST", "CONSTRAINTS"]
    file.write("MINION 3\n")
    for key in minionSectionKeys:
        file.write("**{0}**".format(key) + "\n")
        for value in minionFileSections[key]:
            file.write(value.strip() + "\n")

    file.write("**EOF**")
    file.close()


def encode_negative_table(minionFile, minionSolString):
    minionFileSections = parse_minion_file(minionFile)

    variables = read_minion_variables(minionFileSections)

    # Grab the tuple list from the parsed minion section if it exists
    tuple_list = minionFileSections.get("TUPLELIST", [])

    # If the tuple_list is empty this must be the first time running this minion file. Add the negativetable constraint
    if len(tuple_list) == 0:
        minionFileSections["CONSTRAINTS"].append(
            "negativetable([" + variables + "],negativeSol)"
        )
    # otherwise, remove the first line (negativeSol ...)
    else:
        tuple_list = tuple_list[1:]

    # only update minionFile if minion finds a solution, i.e., a new instance is generated
    if minionSolString != "":
        tuple_list.append(minionSolString)
        tuple_list = list(
            set(tuple_list)
        )  # remove duplicate solutions (shouldn't happen, but sometime it does because of crashed runs or resume)
        minionFileSections["TUPLELIST"] = [
            "negativeSol {0} {1}".format(len(tuple_list), len(variables.split(",")))
        ]
        minionFileSections["TUPLELIST"].extend(tuple_list)
        write_out_modified_minion_file(minionFile, minionFileSections)


def make_conjure_solve_command(
    essenceModelFile,
    eprimeModelFile,
    instFile,
    solver,
    SRTimeLimit=0,
    SRFlags="",
    solverTimeLimit=0,
    solverFlags="",
    seed=None,
):
    # temporary files that will be removed
    lsTempFiles = []

    # SROptions string
    SROptionsStr = ""
    if SRTimeLimit > 0:
        SROptionsStr += "-timelimit " + str(int(SRTimeLimit))
    SROptionsStr += " " + SRFlags

    # solverInfo string
    solverOptionStr = ""

    # solver timelimit
    if not solver in solverInfo:
        raise Exception("Sorry, solver " + solver + " is not yet supported.")
    opts = solverInfo[solver]
    if solverTimeLimit > 0:
        if opts["timelimitUnit"] == "s":
            solverTimeLimit = int(solverTimeLimit)
        elif opts["timelimitUnit"] == "ms":
            solverTimeLimit = int(solverTimeLimit * 1000)
        else:
            raise Exception(
                "ERROR: solver "
                + solver
                + ": timelimitUnit "
                + opts["timelimitUnit"]
                + " not supported"
            )
        solverOptionStr += opts["timelimitPrefix"] + str(solverTimeLimit)

    # solver random seed (only when the solver supports passing a random seed, i.e., solverInfo['randomSeedPrefix'] != None
    if (seed != None) and (opts["randomSeedPrefix"] != None):
        if (
            solver == "cplex"
        ):  # cplex case is special: we need to create a temporary text file to pass the random seed to cplex
            rndSeedCplexFile = instFile + ".cplexseed"
            with open(rndSeedCplexFile, "wt") as f:
                f.write("CPXPARAM_RandomSeed " + str(seed))
            lsTempFiles.append(rndSeedCplexFile)
            solverOptionStr += " --readParam " + rndSeedCplexFile
        else:
            solverOptionStr += " " + opts["randomSeedPrefix"] + str(seed)

    # solver flags
    solverOptionStr += " " + solverFlags

    # conjure solve command
    outDir = os.path.dirname(eprimeModelFile)
    eprimeModelFile = os.path.basename(eprimeModelFile)
    conjureCmd = (
        "conjure solve "
        + essenceModelFile
        + " "
        + instFile
        + " -o "
        + outDir
        + " --use-existing-models="
        + eprimeModelFile
        + ' --savilerow-options "'
        + SROptionsStr
        + '"'
        + ' --solver-options "'
        + solverOptionStr
        + '"'
        + " --solver="
        + solver
    )

    return conjureCmd, lsTempFiles


def call_conjure_solve(essenceModelFile, eprimeModelFile, instFile, setting, seed):
    if "name" in setting:
        solver = setting["name"]
    elif "solver" in setting:
        solver = setting["solver"]
    lsTempFiles = []

    # make conjure solve command line
    conjureCmd, tempFiles = make_conjure_solve_command(
        essenceModelFile,
        eprimeModelFile,
        instFile,
        solver,
        # setting["SRTimeLimit"],
        # setting["SRFlags"],
        # setting["solverTimeLimit"],
        # setting["solverFlags"],
        3,
        "",
        0,
        "",
        seed,
    )
    lsTempFiles.extend(tempFiles)

    # call conjure
    print("\nCalling conjure")
    log(conjureCmd)
    cmdOutput, returnCode = run_cmd(conjureCmd)
    log(cmdOutput)

    status = None
    if (
        ("GC overhead limit exceeded" in cmdOutput)
        or ("OutOfMemoryError" in cmdOutput)
        or ("insufficient memory" in cmdOutput)
    ):
        status = "SRMemOut"
    elif "Savile Row timed out" in cmdOutput:
        status = "SRTimeOut"
    elif "increase MAX_VARS" in cmdOutput:  # what are we checking here???
        status = "SRMemOut"
    elif (
        ("Error: maximum memory exceeded" in cmdOutput)
        or ("Out of memory" in cmdOutput)
        or ("Memory exhausted!" in cmdOutput)
    ):
        status = "solverMemOut"
    elif ("Sub-process exited with error code:139" in cmdOutput) and (
        setting["abortIfSolverCrash"] is False
    ):
        status = "solverCrash"
    elif returnCode != 0:
        raise Exception(cmdOutput)

    baseFile = (
        eprimeModelFile.replace(".eprime", "")
        + "-"
        + os.path.basename(instFile).replace(".param", "")
    )
    infoFile = baseFile + ".eprime-info"
    inforFile = baseFile + ".eprime-infor"
    minionFile = baseFile + ".eprime-minion"
    dimacsFile = baseFile + ".eprime-dimacs"
    fznFile = baseFile + ".eprime-param.fzn"
    mznFile = baseFile + ".eprime.mzn"
    eprimeParamFile = baseFile + ".eprime-param"
    eprimeSolutionFile = glob.glob(baseFile + "*.eprime-solution")
    solutionFile = glob.glob(baseFile + "*.solution")
    solutionFile.extend(
        glob.glob(os.path.basename(baseFile) + ".solution")
    )  # in case conjure doesn't generate essence solution file within the folder of eprime model
    lsTempFiles.extend(
        [
            inforFile,
            minionFile,
            dimacsFile,
            mznFile,
            fznFile,
            eprimeParamFile,
            eprimeSolutionFile,
            solutionFile,
        ]
    )

    print("Waiting for " + infoFile)

    # Wait a maximum of 60s for SR-info file to appear
    if status != "SRMemOut":
        max_wait = 60
        while True:
            if os.path.isfile(infoFile):
                break
            elif max_wait <= 0:
                os.stat(infoFile)
                raise Exception(
                    "Waited max time for SR-info file to appear {0}".format(infoFile)
                )
            else:
                time.sleep(1)
                max_wait -= 1

    if os.path.isfile(infoFile):
        # rename infoFile so that it includes random seed and solver name
        newInfoFile = baseFile + "-seed_" + str(seed) + "-" + solver + ".eprime-info"
        print("Renaming SR info file: " + infoFile + " -> " + newInfoFile)
        if os.path.isfile(infoFile):
            os.rename(infoFile, newInfoFile)
        infoFile = newInfoFile

        # parse SR info file
        infoStatus, SRTime, solverTime = parse_SR_info_file(
            infoFile, timelimit=3
            #  timelimit=setting["solverTimeLimit"]
        )
        if status != "solverCrash":
            status = infoStatus

    delete_file(lsTempFiles)
    return status, SRTime, solverTime


def parse_SR_info_file(fn, knownSolverMemOut=False, timelimit=0):
    lsLines = read_file(fn)

    def get_val(field):
        ls = search_string(field, lsLines)
        if len(ls) > 0:
            return ls[0].split(":")[1].strip()
        else:
            return None

    # initial assumptions
    SRTime = 0
    solverTime = 0
    status = None

    # SR status
    if get_val("SavileRowTimeOut") == "1" or get_val("SavileRowClauseOut") == 1:
        status = "SRTimeOut"

    # SR time and solver time
    if get_val("SavileRowTotalTime") != None:
        SRTime = float(get_val("SavileRowTotalTime"))
    if get_val("SolverTotalTime") != None:
        solverTime = float(get_val("SolverTotalTime"))

    # solver status
    if status != "SRTimeOut":

        # if solver is out of memory because of runsolver, SR will write an info file with solverTimeOut=1. We'll fix it and return.
        if knownSolverMemOut:
            status = "solverMemOut"
            return status, SRTime, solverTime

        if get_val("SolverMemOut") == "1":
            status = "solverMemOut"
        elif get_val("SolverTimeOut") == "1":
            status = "solverTimeOut"
        elif get_val("SolverNodeOut") == "1":
            status = "solverNodeOut"
        else:
            if (
                timelimit > 0 and solverTime > timelimit
            ):  # for the case when solver timeout but SR reports SolverTimeOut=0 (happens with minizinc atm)
                status = "solverTimeOut"
            elif get_val("SolverSatisfiable") == "1":
                status = "sat"
            else:
                status = "unsat"
    return status, SRTime, solverTime
