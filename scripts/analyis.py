import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import sys
import argparse
from collections import Counter


def main():
    parser = argparse.ArgumentParser()

    # general settings
    parser.add_argument(
        "--fileName",
        required=True,
        type=str,
        help="path to the analysis file (json)"
    )

    parser.add_argument(
        "--repair",
        type=bool,
        default=False,
    )

    parser.add_argument(
        "--minTime",
        type=int
    )

    parser.add_argument(
        "--maxTime",
        type=int
    )



    # read all settings into one variable and check setting validity
    args = parser.parse_args()
    with open(args.fileName, 'r') as f:
        f.readline()
        # print(f.readline())
        lsLines = []
        okTimes = []
        okInst = []
        for s in f.readlines():
            data = json.loads(s)
            if args.repair:
                if "genunsat" in data["status"] or "gensolverTimeOut" in data["status"]:
                    lsLines.append(data["status"])
                else:

                    data["instanceResults"]["results"]["main"]["runs"] = sorted(
                        data["instanceResults"]["results"]["main"]["runs"], key=lambda run: run["solverTime"]
                    )
                    nRuns = len(data["instanceResults"]["results"]["main"]["runs"])
                    medianRun = data["instanceResults"]["results"]["main"]["runs"][int(nRuns / 2)]

                    if (medianRun["solverTime"] <= args.minTime):
                        lsLines.append("tooEasy")
                    elif (medianRun["solverTime"] >= args.maxTime):
                        lsLines.append("tooDifficult")
                    else:
                        lsLines.append("ok " + medianRun["status"])
                        okTimes.append(medianRun["solverTime"])
                        okInst.append(data["instanceResults"]["instance"])

            else:
                if "ok" in data["status"]:
                    nRuns = len(data["instanceResults"]["results"]["main"]["runs"])
                    medianRun = data["instanceResults"]["results"]["main"]["runs"][int(nRuns / 2)]
                    if "unsat" in medianRun["status"]:
                        lsLines.append("ok unsat")
                        # print(s)
                    else:
                        lsLines.append("ok sat")
                    okTimes.append(medianRun["solverTime"])
                    okInst.append(data["instanceResults"]["instance"])
                else:
                    lsLines.append(data["status"])
            plt.hist(okInst, okTimes)
            plt.show()
    print(Counter(lsLines).items())
    print (okTimes)


main()
