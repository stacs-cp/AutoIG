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
SCORE_BEST = -9999



# Define constants for outputs
detailedOutputDir = "./detailed-output"

# for minizinc experiments only: solvers where -r doesn't work when being called via minizinc
deterministicSolvers = ["ortools"]