problemType = None

# Define constants for scoring

# General
SCORE_UNWANTED_TYPE = 0
SCORE_TOO_EASY = 0
SCORE_INCORRECT_ANSWER = 0
SCORE_TOO_DIFFICULT = 0

# Graded
SCORE_GRADED = -1

# Discriminating
SCORE_BASE_TOO_EASY = 0
SCORE_FAVOURED_TOO_DIFFICULT = 0
# Best when one can do it but the other can't
SCORE_BEST = -9999



# Define constants for outputs
detailedOutputDir = "./detailed-output"

# for minizinc experiments only: solvers where -r doesn't work when being called via minizinc
deterministicSolvers = ["ortools"]

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
solverInfo["or-tools"] = {
    "timelimitUnit": "s",
    "timelimitPrefix": "-t ",
    "randomSeedPrefix": "--fz_seed=",
}