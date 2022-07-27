import sys
import os
import argparse

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

from minizinc_utils import minizinc_solve

parser = argparse.ArgumentParser(description="Run a solver on an instance via minizinc")
parser.add_argument("-m", type=str, required=True, help="MiniZinc model file")
parser.add_argument("-i", type=str, required=True, help="MiniZinc instance file")
parser.add_argument("-s", type=str, required=True, help="solver")
parser.add_argument("-c", type=str, default=None, help="check solvers")
parser.add_argument("-t", type=int, default=1200, help="time limit")

args = parser.parse_args()

modelFile = args.m
instFile = args.i
solver = args.s
solvers_to_check = None
if args.c is not None:
    solvers_to_check = [s.strip() for s in args.c.split(",")]
timelimit = args.t

modelFile = os.path.abspath(modelFile)
instFile = os.path.abspath(instFile)

status, totalTime, extra = minizinc_solve(
    modelFile=modelFile,
    instFile=instFile,
    solver=solver,
    timeLimit=timelimit,
    solvers_to_check=solvers_to_check,
)
results = {
    "modelFile": os.path.abspath(modelFile),
    "instFile": os.path.abspath(instFile),
    "solver": solver,
    "status": status,
    "time": totalTime,
    "extra": extra,
}
print("\nRun results:")
print(results)
