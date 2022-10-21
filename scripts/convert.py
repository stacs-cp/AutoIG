import os
import json
import argparse

import sys

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

import utils

def convert_essence_instance_to_mzn(
    generatorFile, essenceParamFile, outputMznFile="default"
):
    """
    convert an instance in Essence format to MiniZinc format
    inputs:
        - generatorFile (str): the generator model (in Essence), we need to read this file to recognise the type of each instance param
        - essenceParamFile (str): the instance file written in Essence
    output:
        outputMznFile (str): the converted instance file in MiniZinc format
    """
    
    if outputMznFile == "default":
        outputMznFile = essenceParamFile.replace(".param", ".dzn")
        
    # remove auxiliary variables in the Essence instance file
    auxParamFile = essenceParamFile.replace(".param", ".auxRemoved.param")
    cmd = f"conjure autoig --remove-aux {essenceParamFile} {auxParamFile}"
    print(cmd)
    utils.run_cmd_with_assertion(cmd)
    
    # convert Essence instance file to MiniZinc format
    cmd = f"conjure pretty {auxParamFile} --output-format=minizinc"
    print(cmd)
    output = utils.run_cmd_with_assertion(cmd)
    output = output.replace("Parsing as a parameter file","") # remove conjure's comment
    with open(outputMznFile, "wt") as f:
        f.write(output)
    print(f"{outputMznFile} generated")
    
    # remove temporary file
    os.remove(auxParamFile)