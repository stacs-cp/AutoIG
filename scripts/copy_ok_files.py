import pandas as pd
import numpy as np
import json
import os
import sys
import argparse
from collections import Counter
import shutil

def copyInstFile(srcDir, src, dstDir):
    srcFile = os.path.join(srcDir, src)
    dstFile = os.path.join(dstDir, src)
    shutil.copyfile(srcFile, dstFile)

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
    
    parser.add_argument(
        "--detailedOutDir",
        type=str
    )
    
    parser.add_argument(
        "--outDir",
        type=str,
    )



    # read all settings into one variable and check setting validity
    args = parser.parse_args()
    
    if not os.path.isdir(args.outDir):
        os.mkdir(args.outDir)
    
    satDir = os.path.join(args.outDir, "sat")
    
    if not os.path.isdir(satDir):
        os.mkdir(satDir)
    
    unsatDir = os.path.join(args.outDir, "unsat")
    
    if not os.path.isdir(unsatDir):
        os.mkdir(unsatDir)
        
    with open(args.fileName, 'r') as f:
        f.readline()

        lsLines = []
        for s in f.readlines():
            data = json.loads(s)
            if args.repair:
                if not ("genunsat" in data["status"] or "gensolverTimeOut" in data["status"]):

                    data["instanceResults"]["results"]["main"]["runs"] = sorted(
                        data["instanceResults"]["results"]["main"]["runs"], key=lambda run: run["solverTime"]
                    )
                    nRuns = len(data["instanceResults"]["results"]["main"]["runs"])
                    medianRun = data["instanceResults"]["results"]["main"]["runs"][int(nRuns / 2)]

                    if not (medianRun["solverTime"] <= args.minTime or medianRun["solverTime"] >= args.maxTime):
                        copyInstFile(args.detailedOutDir, os.path.basename(data["instanceResults"]["instance"]), os.path.join(args.outDir, medianRun["status"]))

            else:
                if "ok" in data["status"]:
                    nRuns = len(data["instanceResults"]["results"]["main"]["runs"])
                    medianRun = data["instanceResults"]["results"]["main"]["runs"][int(nRuns / 2)]


main()
