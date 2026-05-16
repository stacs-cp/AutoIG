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

from utils import get_normalised_entropy_score, get_frequency_coverage_score
import math


wantedStats = ["ok"]
# dirs = ['mcd', 'base', 'nonElite', 'random', 'iavgbuc']
# dirs = ['mcd', 'mcdNE', 'base', 'nonElite', 'random', 'randomNE', 'iavgbuc', 'iavgbucNE']
dirs = ['mcd', 'base', 'mcdNE', 'ientropy', 'delta']

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
        default="data120.csv"
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
        default="entropy",
        choices=["entropy", "lex"]
    )

    args = parser.parse_args()

    def getBucket(solverTime):
        normTime = (solverTime - args.minTime) / (args.maxTime - args.minTime) # normalise
        return math.floor(normTime / (1 / args.numBuckets)) # divide into buckets

    allTimes = {}
    bucketCounts = {}
    finalScores = {}

    for problem in dirs:
        config, tRs, tRsNoDup = read_data(os.path.join(args.dir,problem))
        bucketCounts[problem] = [0] * args.numBuckets
        # filter out non-graded instances
        tInfo = tRsNoDup.loc[tRsNoDup.status=="graded",:]

        # calculate average solving time for each instance  
        tInfo.loc[:,"avgSolvingTime"] = [np.mean([rs["time"] for rs in x["results"]["main"]["runs"]]) for x in tInfo.instanceResults]
        allTimes[problem] = tInfo.loc[:,"avgSolvingTime"]

        for time in allTimes[problem]:
            bucketCounts[problem][getBucket(time)] += 1

        if args.metric == "entropy":
            finalScores[problem] = [get_normalised_entropy_score(bucketCounts[problem])]
        else:
            finalScores[problem] = [get_frequency_coverage_score(bucketCounts[problem], 0.5)] 
        
    # print(finalScores)
    df = pd.DataFrame(finalScores)
    df.to_csv(args.out)
main()
