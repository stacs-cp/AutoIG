import seaborn as sns
import pandas as pd
import argparse
from essence_pipeline_utils import calculate_essence_borda_scores
import json

wantedStats = ["ok"]

def main():
    parser = argparse.ArgumentParser()

    # general settings
    parser.add_argument(
        "--fileName",
        required=True,
        type=str,
        help="path to the analysis file (json)"
    )
    args = parser.parse_args()
    with open(args.fileName, 'r') as f:
        f.readline()
        baseScores = []
        favouredScores = []
        for s in f.readlines():
            data = json.loads(s)
            if data["status"] not in wantedStats:
                continue
            else:
                results = data["instanceResults"]
                baseResults = results["base"]["runs"][i]
                favouredResults = results["favoured"]["runs"][i]

                baseScore, favouredScore = calculate_essence_borda_scores(baseResults["status"],
                    favouredResults["status"],
                    baseResults["solverTime"],
                    favouredResults["solverTime"],
                    "SAT",
                    True,
                    )
                baseScores.append(baseScore)
                favouredScores.append(favouredScore)
        sns.boxplot(data=baseScores)