import os
import glob
import subprocess
import shlex
import datetime
import shutil
import numpy as np
import math


# Calculate the integral distance between a uniform CDF and some other distribution
# Assumes other dataset is normalised between [0, 1]
def get_wasserstein_distance_area(normalisedTimes):
    """
    Calculate the Wasserstein distance between the uniform cumulative distribution function and a list of normalised solving times as a CDF.

    normalisedTimes -- A list of points between [0,1] that represents the solving times of the instance set, with each point carrying equal probability weight

    Returns the Wasserstein distance as the area between the two CDFs in a single float
    """
    # uniform cdf -> y = x
    normalisedTimes.sort()

    # calculate the probability mass to assign to each point
    # Each point represents the same probability mass
    numInstances = len(normalisedTimes)
    interval = 1 / numInstances

    areas = []

    # calculate first triangle
    areas.append(normalisedTimes[0] * normalisedTimes[0])
    
    # calculate final triangle
    areas.append(math.pow((1-normalisedTimes[-1]), 2))

    # for each step in between, calculate the integral
    for i in range(0, numInstances - 1):

        intersection = (i+1) / numInstances # calculate the height (y) of this step

        # case where intersection is between the range, forms to triangles above and below
        if normalisedTimes[i] < intersection < normalisedTimes[i+1]:
            firstTriangleBnH = intersection - normalisedTimes[i]

            secondTriangleBnH = normalisedTimes[i+1] - intersection

            areas.append(firstTriangleBnH * firstTriangleBnH)
            areas.append(secondTriangleBnH * secondTriangleBnH)
        # case where intersection is the edge of a range, forms one triangle
        elif (normalisedTimes[i] == intersection) or (normalisedTimes[i+1] == intersection):
            areas.append(math.pow(normalisedTimes[i+1] - normalisedTimes[i], 2))
        else: # case for trapezoid where no intersection happens
            height = abs(normalisedTimes[i+1] - normalisedTimes[i])
            base1 = abs(intersection - normalisedTimes[i])
            base2 = abs(intersection - normalisedTimes[i+1])
            areas.append(height * ((base1 + base2)))
        

    # divide by half for area
    return sum(areas) * 0.5



def get_normalised_entropy(binCounts):
    """
    Return the normalised Shannon entropy given the frequency count in each bin.

    binCounts -- A list of frequencies in each bin including the empty bins.

    Returns the normalised Shannon entropy as a float
    """
    nm = sum(binCounts) # total number of instances
    
    p = []
    for c in binCounts:
        if c != 0: # filter out zeroes to avoid log(0)
            p.append(c / nm)
            
    # sum( p * log(p))
    entropy = np.sum(p * np.log(p)) 
    
    # divide by log(# of buckets) for normalised entropy value
    Hnorm = - entropy / np.log(len(binCounts)) 
    return Hnorm.item()

def log(logMessage):
    print(
        "{0}: {1}".format(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), logMessage
        )
    )


def read_file(fn):
    lsLines = []
    with open(fn, "rt") as f:
        lsLines = [line.rstrip("\n") for line in f]

    return lsLines


def search_string(s, lsStrs):
    lsOut = []
    for line in lsStrs:
        if s in line:
            lsOut.append(line)
    return lsOut


def run_cmd(cmd, printOutput=False, outFile=None):
    lsCmds = shlex.split(cmd)
    p = subprocess.run(lsCmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = p.stdout.decode("utf-8")
    if outFile is not None:
        with open(outFile, "wt") as f:
            f.write(output)
    if printOutput:
        print(output)
    return output, p.returncode

def run_cmd_with_assertion(cmd):
    output, rc = run_cmd(cmd)
    assert rc==0, f"ERROR: command '{cmd}' does not run correctly. Output is: \n{output}\n. \nReturn code: {rc}"
    return output


def delete_file(fn):
    if isinstance(fn, list):  # delete a list of files
        for name in fn:
            if isinstance(name, list):
                delete_file(name)
            elif os.path.isfile(name):
                os.remove(name)
    else:  # delete by pattern
        lsFile = glob.glob(fn)
        for fn in lsFile:
            os.remove(fn)


def get_conjure_version():
    if shutil.which("conjure") is None:
        return None
    ls, _ = run_cmd("conjure --help", printOutput=False)
    ls = ls.split("\n")
    s = [s for s in ls if "Repository version" in s][0]
    conjureVersion = s.split(" ")[2]
    return conjureVersion


def get_SR_version():
    if shutil.which("savilerow") is None:
        return None
    ls, _ = run_cmd("savilerow -help", printOutput=False)
    ls = ls.split("\n")
    s = [s for s in ls if "Repository Version" in s][0]
    srVersion = s.split(" ")[5]
    return srVersion


def get_minizinc_version():
    if shutil.which("minizinc") is None:
        return None
    ls, _ = run_cmd("minizinc --version", printOutput=False)
    ls = ls.split("\n")
    ls = [s for s in ls if "version " in s]
    if len(ls) > 0:
        mznVersion = ", ".join(ls[1:])
        return mznVersion
    else:
        return ""
