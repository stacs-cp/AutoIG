from functools import cmp_to_key
import subprocess
import math
import random

# Import minizinc pipeline functions 
from minizinc_utils import minizinc_solve, run_comparator, get_minizinc_problem_type, has_better_objective

# Import configurations file for using constants
import conf
from wrapper_helpers import read_setting

from utils import get_normalised_entropy_score

from filelock import FileLock

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
            score = conf.SCORE_UNWANTED_TYPE
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
                score = conf.SCORE_INCORRECT_ANSWER
                status = "inconsistentInstanceTypes"
                return score, get_results()

        # update optimal objective & check for inconsistency
        if (runStatus == "C") and (instanceType == "sat"):
            if optimalObj is None:
                assert len(extra["objs"]) > 0
                optimalObj = extra["objs"][-1][1]
            elif optimalObj != extra["objs"][-1][1]:
                print("Inconsistent optimal objective value between runs. Quitting...")
                score = conf.SCORE_INCORRECT_ANSWER
                status = "inconsistentOptimalValues"
                return score, get_results()

        # if the instance is of an unwanted type, we stop immediately
        if len(unwantedTypes) > 0 and instanceType and (instanceType in unwantedTypes):
            print("Unwanted instance type. Quitting...")
            score = conf.SCORE_UNWANTED_TYPE
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
    # For satisfiable problems we can accept incomplete search status "S", for optimisation problems results must be complete or "C"
    if (medianRun["status"] in (["C", "S"] if problemType == "SAT" else ["C"])) and (medianRun["time"] < minTime):
        print("Instance too easy. Quitting...")
        score = conf.SCORE_TOO_EASY
        status = "tooEasy"
        return score, get_results()

    # if the instance is unsolvable by the main solver, there's no need to run the oracle
    # For satisfiable problems we can allow for incomplete searchers, but for optimising problems we must have complete searches
    if medianRun["status"] not in (["S", "C"] if problemType == "SAT" else ["C"]):
        print("Instance too difficult. Quitting...")
        score = conf.SCORE_TOO_DIFFICULT
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
            score = conf.SCORE_TOO_DIFFICULT
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
                score = conf.SCORE_INCORRECT_ANSWER
                status = "incorrectInstanceType"
                return score, get_results()
            # objective value
            if (r["status"] in ["S", "C"]) and (oracleExtra["instanceType"] == "sat"):
                assert len(r["extra"]["objs"]) > 0
                optimal = oracleExtra["objs"][-1][1]
                for o in r["extra"]["objs"]:
                    if has_better_objective(o[1], optimal, problemType):
                        print("Incorrect results (checked by oracle). Quitting...")
                        score = conf.SCORE_INCORRECT_ANSWER
                        status = "incorrectObjectiveValue"
                        return score, get_results()
                if (r["status"] == "C") and (r["extra"]["objs"][-1][1] != optimal):
                    print("Incorrect results (checked by oracle). Quitting...")
                    score = conf.SCORE_INCORRECT_ANSWER
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
                score = conf.SCORE_TOO_DIFFICULT
                status = "tooDifficult"
                return score, get_results()
            else:
                lastTime = medianRun["extra"]["objs"][-1][0]
                # if the main solver is incomplete and the optimal value is reached within in less than minTime seconds, consider the instance as too easy
                if lastTime < minTime:
                    print("Instance too easy. Quitting...")
                    score = conf.SCORE_TOO_EASY
                    status = "tooEasy"
                    return score, get_results()

    settings = read_setting("./config.json")
    metric = settings["generalSettings"]["diversityMetric"]

    if (metric == "max_closest_dist" or metric == "maxAvgDist"):
        # hashing config file to get file lock name unique to this run
        hashProcess = subprocess.run("sha256sum config.json | awk '{print $1}'", shell=True, stdout=subprocess.PIPE)
        hash = hashProcess.stdout.decode('utf-8').strip()

        # define file lock
        lock = FileLock(f"{hash}.lock")
        
        data = []
        instance = instFile.replace(".dzn", "")
        seed = instance.split("-")[-1]
        
        def normalise(maxVal, minVal, val):
            return ((val - minVal) / (maxVal - minVal))


        # request lock
        with lock:
            with open("diversity.txt", "r+") as f:
                
                data = f.read().strip().split("\n") # read the data and split into separate file data
                f.write(f"{instance},{medianRun["time"]}\n")
        
        # release lock once read data and written current time
        
        def filterFunc(x):
            if(x == ''):
                return False
            return not (seed == x.split("-")[-1].split(",")[0]) # isolate the seed
        
        # filter out any instances that have the same seed (same run)
        filteredData = list(filter(filterFunc, data))

        if len(filteredData) == 0: # if there is no data, then no information can be gained so -1 to still have distinction btwn graded but unranked and non-graded
            score = -1
            status="ok"
            return score, get_results()

        differences = []

        # Get the absolute differences between the current item and all remaining times
        for entry in filteredData:
            entryTime = float(entry.split(",")[-1]) #extract runtime from entry
            differences.append(round(abs(entryTime - medianRun["time"]), 2))
        
        if metric == "max_closest_dist":
            # flatten to 0-1 by dividing the range of difference, then obtain the decimal bucket the difference is in
            # currently only to the granularity of 10 buckets so working in decimal
            diffNormal = list(map(lambda x : int(math.floor((x / (timeLimit - minTime))* 10)), differences))
            
            # zero pad the number in case array size smaller than 10
            if len(diffNormal) < 10:
                padLen = 10 - len(diffNormal)
                diffNormal = diffNormal + [0] * padLen
            
            # sort from smallest to largest to get closest neigbours
            diffNormal.sort(reverse=False)
            diffNormal = diffNormal[:10]
            # get the negative integer result of concatenating all the inidividual buckets
            result = - int("".join(str(val) for val in diffNormal))
            # averageDiff = sum(differences) / len(differences)

            score = result
        elif metric == "maxAvgDist":
            # normalise differences to range between 0-1
            diffNormal = list(map(lambda x: (x / (timeLimit - minTime)), differences))
            
            # get the average distance between the current time and all previous times
            avgDist = sum(diffNormal) / len(diffNormal)
            score = -avgDist

    elif (metric == "none"):
        score = -1
    elif (metric == "random"):
        instance = instFile.replace(".dzn", "")
        seed = instance.split("-")[-1]
        random.seed(seed)
        score = random.randint(-100, -1)
    elif (metric == "individualAvgBuckets" or metric == "individualNormEntropy"):
        # hashing config file to get file lock name unique to this run
        hashProcess = subprocess.run("sha256sum config.json | awk '{print $1}'", shell=True, stdout=subprocess.PIPE)
        hash = hashProcess.stdout.decode('utf-8').strip()

        # define file lock
        lock = FileLock(f"{hash}.lock")
        
        data = []
        instance = instFile.replace(".dzn", "")
        seed = instance.split("-")[-1]
        genInstID = instance.split("-")[-2]
        
        # request lock
        with lock:
            with open("diversity.txt", "r+") as f:
                
                data = f.read().strip().split("\n") # read the data and split into separate file data
                f.write(f"{instance},{medianRun["time"]}\n")
        
        # release lock once read data and written current time
        
        def filterFunc(x):
            if(x == ''):
                return False
            return (genInstID == x.split("-")[-2]) # isolate the generator instance ID
        
        # keep any data from the same generator instance
        filteredData = list(filter(filterFunc, data))

        # measure of granularity, how many buckets to divide the acceptable (graded) time range into
        numBuckets = 20
        buckets = [0] * numBuckets # create an array representing buckets

        def getBucket(solverTime):
            normTime = (solverTime - minTime) / (timeLimit - minTime) # normalise
            return math.floor(normTime / (1 / numBuckets)) # divide into buckets

        if (metric == "individualAvgBuckets"):

            if len(filteredData) == 0: # if there is no data, first time this generator found an instance
                score = -0.5 # set to .5 so that prioritise generators that have found over 50% instances in different buckets, but otherwise priorities novelty
                status="ok"
                return score, get_results()
            
            buckets[getBucket(medianRun["time"])] = 1 # set bucket that current time sits in to be true

            for entry in filteredData:
                entryTime = float(entry.split(",")[-1]) #extract runtime from entry
                buckets[getBucket(entryTime)] = 1

            # score is the number of buckets over the number of instances seen
            score = - (sum(buckets) / (len(filteredData) + 1)) # normalise over number of instances seen, +1 for current
        
        elif (metric == "individualNormEntropy"):

            temp = getBucket(medianRun["time"])
            print("bucket number: ", temp)


            buckets[getBucket(medianRun["time"])] += 1 # add one to the current bucket
            
            for entry in filteredData:
                entryTime = float(entry.split(",")[-1]) #extract runtime from entry
                buckets[getBucket(entryTime)] += 1
            
            score = (- get_normalised_entropy_score(buckets)) - 1 # make negative for minimise and also shift by -1 for gradedness

    status = "ok"
    return score, get_results()

