import pandas as pd
import numpy as np
import json
import os
import sys
import argparse
from collections import Counter
from utils import run_cmd, log


def main():
    parser = argparse.ArgumentParser()
    counter = Counter([])
    # general settings
    parser.add_argument(
        "--dirName",
        required=True,
        type=str,
        help="path to the analysis directory containing param files"
    )

    args = parser.parse_args()
    if os.path.isdir(args.dirName):
        files = filter(lambda x : x.endswith('.param') and x.startswith('gen-inst'), os.listdir(args.dirName) )
        for file in files:
            cmd = "conjure solve " + os.path.join(args.dirName, file) + " -o temp --solver-options \"-timelimit 15\""
            cmdOutput, returnCode = run_cmd(cmd)
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
                    for line in cmdOutput.split("\n"):
                        if "Copying solution to:" in line:
                            solFileName = line.replace("Copying solution to: ", "").strip()
                            if os.path.isfile(solFileName):
                                os.remove(solFileName)
                    status = "sat"
            counter.update([status])
            
    print(counter.items())
        


main()

