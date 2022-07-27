import json
import pandas as pd
import ast
import sys
import numpy as np

import sys
import os

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

from minizinc_utils import calculate_minizinc_borda_scores, get_minizinc_problem_type

pd.options.mode.chained_assignment = None

def read_config(configFile):
    """ 
    read configuration file (in .json format)
    """
    with open(configFile, "r") as f:
        config = json.load(f)
    return config


def read_data(runDir):
    """
    read all results and put them into a table
    remove duplicate instances
    Returns:
        - config: experiment settings
        - tRs: detailed results of all runs
        - tRsNoDup: detailed results of all runs but rows that belong to the same instance (duplicates) are removed.
    """
    detailedResultsFile = f"{runDir}/detailed-output/detailed-results.json"
    hashSumFile = f"{runDir}/detailed-output/instance-md5sum.csv"
    configFile = f"{runDir}/config.json"
    
    config = read_config(configFile)

    # read detailed-results.json
    with open(detailedResultsFile, "rt") as f:
        lsLines = [s[:-1] for s in f.readlines() if s.startswith('{"totalTime"')]
        r = [ast.literal_eval(s) for s in lsLines]
    tRs = pd.DataFrame(r)
    tRs["score"] = tRs["score"].astype(float)

    # move generator instance names into a separate column
    tRs.loc[:,"genInstance"] = [s["instance"] for s in tRs.genResults]
    tRs.loc[:,"genResults"] = [(s,s.pop("instance"))[0] for s in tRs.genResults]

    # move candidate instance names into a separate column
    tRs.loc[:,"instance"] = [s["instance"]  if s!={} else None for s in tRs.instanceResults]
    tRs.loc[:,"instanceResults"] = [(s,s.pop("instance"))[0] if s!={} else None for s in tRs.instanceResults]

    # shorten candidate instance names
    tRs.loc[:,"instance"] = [inst.split("detailed-output/")[1] if inst!=None else None for inst in tRs.instance]

    # read instance hashsum
    tHs = pd.read_csv(hashSumFile)

    # add instance hashsum into tRs
    tRs = tRs.merge(tHs,on="instance", how="left")



    # rename status column so it's easier to read
    if config["instanceSetting"]=="graded":
        tRs.loc[:,"status"] = ["graded" if s=="ok" else s for s in tRs.status]
    else:
        def rename_status_dis(status, score):
            if status=="ok":
                if score < -1:
                    return "favouredSolverWins"
                else:
                    return "baseSolverWins"
            else:
                return status
        tRs.loc[:,"status"] = [rename_status_dis(s[0],s[1]) for s in zip(tRs.status,tRs.score)]
        #display(tRs[tRs.status.str.contains("Wins")])
    
    # rename some columns and re-order the columns
    tRs.rename(columns={"hashValue":"instanceHashValue","score":"iraceScore"}, inplace=True)
    tRs = tRs[["genInstance","instance","genResults","instanceResults","status","iraceScore","totalTime","instanceHashValue"]]

    # create a copy of tRs where duplicate instances are removed
    tRsNoDup = tRs.groupby(["instanceHashValue"]).first().reset_index()

    return config, tRs, tRsNoDup


def print_stats(config, tRs, tRsNoDup):
    """
    print summary statistics of an instance generation experiment
    """
        
    # number of finished runs
    nFinishedRuns = len(tRs)
    
    # number of instances generated
    nInstances = len(tRsNoDup.instance.unique())

    # number of runs for each run status
    runStats = tRs.groupby('status').genResults.count().to_dict()
    runStatsWithoutDuplicates = tRsNoDup.groupby('status').genResults.count().to_dict()

    # description of each run status that are commonly used for both graded and discriminating experiments
    runStatNamesCommon = {"genSRTimeOut": "#runs with unsolved generator instances (Savile Row timeouts)",
                    "gensolverTimeOut": "#runs with unsolved generator instances (minion timeouts)",
                    "genunsat": "#runs with unsolved generator instances (UNSAT)",
                    "unwantedType": "#runs with invalid instance type"}

    # description of each run status that are used for graded experiments only
    runStatNamesGraded = {"graded": "#graded instances",                                
                          "tooEasy": "#too easy instances", 
                          "tooDifficult": "#too difficult instances",                 
                          "solverCrash": "#instances where solvers were crashed",
                          "inconsistentInstanceTypes": "#instances with inconsistent answers (regarding satisfiability) across runs", #only valid when nRunsPerInstances>1
                          "inconsistentOptimalValues": "#instances with inconsistent answers (regarding the optimal solution quality) across runs", #only valid when nRunsPerInstances>1
                          "tooDifficultOracle": "#instances where the oracle fails to check the validity of the solver's answer", #only valid for incomplete solvers
                          "incorrectInstanceType": "#instances with incorrect answers (regarding satisfiability)",
                          "incorrectObjectiveValue": "#instances with incorrect optimality reported (better than the true optimal)",
                          "incorrectOptimalValue": "#instances with incorrect optimality reported (different from the true optimal)",
                         }

    # description of each run status that are used for discriminating experiments only
    runStatNamesDis = {"favouredTooDifficult": "#too difficult instances for the favoured solver",
                          "baseTooEasy": "#too easy instances for the base solver", 
                          "favouredSolverWins": "#instances where the favoured solver wins",
                          "baseSolverWins": "#instances where the base solver wins"
                         }

    # print run status statistics
    print("\n")
    print(f"Total #runs: {nFinishedRuns}")
    print(f"Total #instances generated: {nInstances}")
    print("")
    for key, val in runStatsWithoutDuplicates.items():
        if key in runStatNamesCommon:
            print(f"{runStatNamesCommon[key]}: {val} (/{runStats[key]} runs)")
        elif key in runStatNamesGraded:
            print(f"{runStatNamesGraded[key]}: {val} (/{runStats[key]} runs)")
        elif key in runStatNamesDis:
            print(f"{runStatNamesDis[key]}: {val} (/{runStats[key]} runs)")
        else:
            print(f"{key}: {val} (/{runStats[key]} runs)")
  

def extract_graded_and_discriminating_instances(runDir):
    """ 
    extract information about graded/discriminating instances and save to a .csv file
    """
    outFile = None
    if config["instanceSetting"] == "graded":
        # filter out non-graded instances
        tInfo = tRsNoDup.loc[tRsNoDup.status=="graded",:]
        # extract instance type
        tInfo.loc[:,"instanceType"] = [x["results"]["main"]["runs"][0]["extra"]["instanceType"] for x in tInfo.instanceResults]
        # calculate average solving time for each instance  
        tInfo.loc[:,"avgSolvingTime"] = [np.mean([rs["time"] for rs in x["results"]["main"]["runs"]]) for x in tInfo.instanceResults]        
        # re-order columns
        tInfo = tInfo[["instance","instanceType","avgSolvingTime","instanceResults","genInstance","genResults","status","iraceScore","totalTime","instanceHashValue"]]
        # save to a .csv file
        outFile = f"{runDir}/graded-instances-info.csv"
        print(f"\nInfo of graded instances is saved to {os.path.abspath(outFile)}")
        tInfo.to_csv(outFile, index=False)
    else:
        # filter out non-discriminating instances or instances where the favoured solver lost
        tInfo = tRsNoDup.loc[tRsNoDup.status.isin(["favouredSolverWins"]),:]
        # extract instance type
        tInfo.loc[:,"instanceType"] = [x["results"]["favoured"]["runs"][0]["extra"]["instanceType"] for x in tInfo.instanceResults]
        # extract MiniZinc Borda score of the favoured and the base solvers
        problemType = get_minizinc_problem_type(config["problemModel"])
        def extract_minizinc_score(r):
            results = calculate_minizinc_borda_scores(r['base']['runs'][0]['status'], r['favoured']['runs'][0]['status'],
                                       r['base']['runs'][0]['time'], r['favoured']['runs'][0]['time'],
                                        problemType,
                                       r['base']['runs'][0]['extra']['objs'], r['favoured']['runs'][0]['extra']['objs'],
                                       True)
            scores = results["complete"] # first element: base solver's score, second element: favoured solver's score        
            return scores[1]
        tInfo.loc[:,"favouredSolverMiniZincScore"] = [extract_minizinc_score(x["results"]) for x in tInfo.instanceResults]
        tInfo.loc[:,"baseSolverMiniZincScore"] = [1 - x for x in tInfo.favouredSolverMiniZincScore]    
        tInfo.loc[:,"discriminatingPower"] = tInfo["favouredSolverMiniZincScore"] / tInfo["baseSolverMiniZincScore"]
        # re-order columns
        tInfo = tInfo[["instance","discriminatingPower","favouredSolverMiniZincScore","baseSolverMiniZincScore","instanceType","instanceResults","genInstance","genResults","status","iraceScore","totalTime","instanceHashValue"]]
        # save to a .csv file
        outFile = f"{runDir}/discriminating-instances-info.csv"
        print(f"\nInfo of discriminating instances is saved to {os.path.abspath(outFile)}")
        tInfo.to_csv(outFile, index=False)
    
    return tInfo
    
if __name__ == "__main__":
    runDir = sys.argv[1]
    config, tRs, tRsNoDup = read_data(runDir)
    print_stats(config, tRs, tRsNoDup)
    extract_graded_and_discriminating_instances(runDir)    
