import datetime
import os
import sys
import argparse
from shutil import copyfile
from shutil import copy
from shutil import move
import json
import subprocess
import shlex
from collections import OrderedDict

scriptDir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptDir)

import utils
from utils import log

def setup_tuning_folder(args, argGroups):
    # convert all path args to absolute paths
    for argName in ['runDir', 'modelFile', 'generatorFile', 'evaluationSettingFile', 'targetRunner', 'scenario']:
        if getattr(args, argName):
            setattr(args, argName, os.path.abspath(getattr(args, argName)))    

    # create runDir
    if os.path.isdir(args.runDir):
        print("WARNING: directory " + args.runDir + " already exists")
    else:
        os.mkdir(args.runDir)

    # get type of problem specification
    problemModelType = os.path.basename(args.modelFile).split('.')[-1]
    assert problemModelType in ['mzn','essence'], "ERROR: modelFile must end with either .essence or .mzn"

    # copy problem model to runDir
    problemModelFile = args.runDir + '/problem.' + problemModelType
    copyfile(args.modelFile, problemModelFile)

    # remove .conjure-checksum file, otherwise error will be thrown if the script is run more than once
    try:
        os.remove(args.runDir + '/.conjure-checksum')
    except OSError:
        pass
    
    # create a generator automatically from an Essence problem model via conjure
    # params.irace and repair.essence will be generated automatically by conjure
    generatorModelFile = args.runDir + '/generator.essence'
    repairModelFile = None
    if args.generatorFile is None:
        assert problemModelType == 'essence', "ERROR: automated generator model is only supported if modelFile is in Essence"
        
        # run "conjure parameter-generator"
        if args.maxint <= 0:
            print("ERROR: --maxint must be positive")
            sys.exit(1)
        cmd = 'conjure parameter-generator ' + problemModelFile + ' --MAXINT=' + str(args.maxint)
        log(cmd)
        run_cmd(cmd)

        # rename generator spec

        move(problemModelFile.replace('.essence','-instanceGenerator.essence'), generatorModelFile)

        # rename irace param file
        move(problemModelFile.replace('.essence','-instanceGenerator.essence.irace'), args.runDir+'/params.irace')

        # rename repair spec
        oldRepairModelFile = problemModelFile.replace('.essence','-instanceRepair.essence')
        if os.path.isfile(oldRepairModelFile):
            repairModelFile = args.runDir + '/repair.essence'
            move(problemModelFile.replace('.essence','-instanceRepair.essence'), repairModelFile)

    # a generator model is already provided
    else:
        # copy the generator model to runDir
        copyfile(args.generatorFile, generatorModelFile)

        # TODO: we need to generate params.irace and repair.essence based on the provided generator model (at the moment, users have to create those files manually and put them in runDir)
        iraceParamFile = args.runDir + "/params.irace"
        assert os.path.isfile(iraceParamFile), "ERROR: params.irace is missing"

        if os.path.isfile(args.runDir + "repair.essence"):
            repairModelFile = args.runDir + "repair.essence"


    # generate problem's eprime model
    if problemModelType == 'essence':
        conjureTempDir = args.runDir + '/conjure-output'
        cmd = 'conjure modelling -ac ' + problemModelFile + ' -o ' + args.runDir
        log(cmd)
        utils.run_cmd(cmd)
        move(args.runDir + '/model000001.eprime', args.runDir + '/problem.eprime')

    # generate generator's eprime models
    cmd = 'conjure modelling -ac ' + generatorModelFile + ' -o ' + args.runDir
    log(cmd)
    utils.run_cmd(cmd)
    move(args.runDir + '/model000001.eprime', args.runDir + '/generator.eprime') 

    # generate repair's eprime model
    if repairModelFile:
        cmd = 'conjure modelling -ac ' + repairModelFile + ' -o ' + args.runDir
        log(cmd)
        run_cmd(cmd)        
        move(args.runDir + '/model000001.eprime', args.runDir + '/repair.eprime') 

    # create detailed-output folder and copy all .eprime models file into it
    detailedOutDir = args.runDir + '/detailed-output'
    if os.path.isdir(detailedOutDir) is False:
        os.mkdir(detailedOutDir)
        for fn in ['problem.essence','problem.eprime','generator.eprime','repair.eprime']:
            if os.path.isfile(args.runDir + '/' + fn):
                copy(args.runDir + '/' + fn, detailedOutDir)
    
    # copy other neccessary files
    for fn in ['instances','run.sh']:
        copy(scriptDir + '/' + fn, args.runDir)

    # update fields in run.sh
    pbsFile = args.runDir + '/run.sh'
    dictValues = {'seed': args.seed, 'nCores': args.nCores, \
                    'maxExperiments': args.maxExperiments,\
                    'targetRunner': args.targetRunner,\
                    'scenario': args.scenario}
    with open(pbsFile,'rt') as f:
        lsLines = f.readlines()
    for field, value in dictValues.items():
        lsLines = [s.replace('<'+field+'>',str(value)) for s in lsLines]
    with open(pbsFile,'wt') as f:
        f.writelines(lsLines)

    # read evaluation settings
    with open(args.evaluationSettingFile, 'rt') as f:
        evalSettings = json.load(f)    

    # write all settings to setting.json
    settingFile = args.runDir + '/setting.json'
    settings = OrderedDict({})
    for group in argGroups.keys():
        settings[group] = OrderedDict()
        for argName in argGroups[group]:
            settings[group][argName] = getattr(args,argName)
    settings['conjure-version'] = utils.get_conjure_version()
    settings['savilerow-version'] = utils.get_SR_version()
    if problemModelType == 'mzn':
        settings['minizinc-version'] = utils.get_minizinc_version()
    settings['evaluationSettings'] = evalSettings
    with open(settingFile,'wt') as f:
        json.dump(settings, f, indent=True)


def main():
    parser = argparse.ArgumentParser(description='Set up a tuning experiment for automated instance generation')    

    # general settings
    parser.add_argument('--runDir',default='./',help='directory where the experiment will be run')
    parser.add_argument('--modelFile',required=True,help='path to a problem specification file in Essence/MiniZinc')
    parser.add_argument('--generatorFile',default=None,help='path to a generator specification file in Essence')
    parser.add_argument('--experimentType',required=True,choices=['graded','discriminating'])
    parser.add_argument('--evaluationSettingFile',required=True,help='a JSON file specifying solver settings for the experiment')    
    argGroups = OrderedDict({'generalSettings':['runDir','modelFile','generatorFile','experimentType','evaluationSettingFile']})

    # tuning settings
    parser.add_argument('--maxint',default=100,type=int)
    parser.add_argument('--seed',default=123)
    parser.add_argument('--maxExperiments',default=5000,type=int,help='maximum number of evaluations used by the tuning')
    parser.add_argument('--nCores',default=1,type=int,help='how many processes running in parallel for the tuning')
    argGroups['tuningSettings'] = ['maxint','seed','maxExperiments','nCores']

    # generator settings
    parser.add_argument('--genSRTimelimit',default=300,help='SR time limit on each generator instance (in seconds)')
    parser.add_argument('--genSRFlags',default='-S0',help='SR extra flags for solving generator instance')
    parser.add_argument('--genSolverTimelimit',default=300,help='time limit for minion to solve a generator instance (in seconds)')
    argGroups['generatorSettings'] = ['genSRTimelimit','genSRFlags','genSolverTimelimit']

    # read from command line args
    args = parser.parse_args()

    # add fixed general settings
    setattr(args, 'targetRunner', scriptDir + '/target-runner')
    setattr(args, 'scenario', scriptDir + '/scenario.R')
    argGroups['generalSettings'].append('targetRunner')
    argGroups['generalSettings'].append('scenario')
    
    # add fixed generator settings
    setattr(args, 'genSolver','minion')
    #setattr(args, 'genSolverFlags', '-varorder domoverwdeg -valorder random -randomiseorder')
    setattr(args, 'genSolverFlags', '-varorder domoverwdeg -valorder random')
    argGroups['generatorSettings'].extend(['genSolver','genSolverFlags'])

    # set up tuning directory
    setup_tuning_folder(args, argGroups)


main()
