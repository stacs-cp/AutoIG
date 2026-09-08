import seaborn as sns
import pandas as pd
import argparse
import matplotlib.pyplot as plt
from collect_results import read_data
import json
import os
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib

from utils import get_normalised_entropy, get_wasserstein_distance_area
import math


wantedStats = ["ok"]
# dirs = ['mcd', 'base', 'nonElite', 'random', 'iavgbuc']
# dirs = ['mcd', 'mcdNE', 'base', 'nonElite', 'random', 'randomNE', 'iavgbuc', 'iavgbucNE']
# dirs = ['individualNormEntropy']
def main():
    parser = argparse.ArgumentParser()

    # general settings
    parser.add_argument(
        "--dir",
        default=".",
        type=str,
        help="path to the analysis file (json)"
    )
    parser.add_argument(
        "--minTime",
        type=float,
        default=10
    )
    parser.add_argument(
        "--maxTime",
        type=float,
        default=1200
    )
    parser.add_argument(
        "--out",
        default="test.csv"
    )

    parser.add_argument(
        "--title",
        default="Instance Solving Time using Chuffed on Macc",
    )

    parser.add_argument(
        "--numBuckets",
        type=int,
        default=120
    )

    parser.add_argument(
        "--metric",
        default="wasserstein",
        choices=["entropy", "lex", "wasserstein", "wasserstein_linear"]
    )

    args = parser.parse_args()

    def getBucket(solverTime):
        # if solverTime > 1200 and solverTime < 1202: # account for slight deviations
        #     solverTime = 1199.99999999
        normTime = (solverTime - args.minTime) / (args.maxTime - args.minTime) # normalise
        return math.floor(normTime / (1 / args.numBuckets)) # divide into buckets

    def normaliseTime(time):
        normTime = (time - args.minTime) / (args.maxTime - args.minTime) # normalise
        return normTime

    

    solvers = ["ortools", 'chuffed']
    problems = ['macc', 'lot-sizing', 'carpet-cutting', 'mario', 'racp']
    seeds = [11, 22, 33, 44, 55, 66, 77, 42, 48, 86]
    
    # solvers = ['chuffed']
    # problems = ['mario']
    # seeds = [55]
    collectDir = 'AAAI27Data'
    dirs = ['max_closest_dist', 'none', 'individualNormEntropy', 'normalisedEntropyDelta', 'wassersteinDelta']

    # seeds = [11, 22, 42, 48, 86]
    # seeds = [55]
    

    for solver in solvers:
        for problemClass in problems:

            allTimes = {}
            bucketCounts = {}
            finalScores = {}
            finalScoresWass = {}
            finalScoresEntr = {}
            for problemBase in dirs:
                for problemSeed in seeds:
                    problem = problemBase+str(problemSeed)
                    print(f"working on {solver} {problemClass} {problem}")
                    config, tRs, tRsNoDup = read_data(os.path.join(solver, problemClass, args.dir,problem))
                    bucketCounts[problem] = [0] * args.numBuckets
                    # filter out non-graded instances
                    tInfo = tRsNoDup.loc[tRsNoDup.status=="graded",:]
                    # calculate average solving time for each instance  
                    tInfo.loc[:,"avgSolvingTime"] = [np.mean([rs["time"] for rs in x["results"]["main"]["runs"]]) for x in tInfo.instanceResults]
                    allTimes[problem] = tInfo.loc[tInfo["avgSolvingTime"] <= args.maxTime,"avgSolvingTime"]

                    for time in allTimes[problem]:
                        # if problem == "none66":
                        #     print(time)
                        bucketCounts[problem][getBucket(time)] += 1
                    if len(allTimes[problem]) == 0:
                        print(f"NO INSTANCES FOUND FOR: {solver} {problemClass} {problem}")
                    else:

                        finalScores[problem] = {
                            "Number of Instances": len(allTimes[problem]), 
                            "Normalised Entropy Score": get_normalised_entropy(bucketCounts[problem]),
                            "Wasserstein Distance": get_wasserstein_distance_area(list(map(lambda x: normaliseTime(x), allTimes[problem])))
                            }

                    
            # print(finalScores)
            df = pd.DataFrame(finalScores)
            df.transpose().to_csv(os.path.join(collectDir, 'raws', f'{solver}_{problemClass}_summarised.csv'))
main()
