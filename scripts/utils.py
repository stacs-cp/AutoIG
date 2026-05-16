import os
import glob
import subprocess
import shlex
import datetime
import shutil
import numpy as np

def get_normalised_entropy(binCounts):
    nm = sum(binCounts) # total number of instances
    
    p = []
    for c in binCounts:
        if c != 0: # filter out zeroes to avoid log(0)
            p.append(c / nm)
            
    # sum( p * log(p))
    entropy = np.sum(p * np.log(p)) 
    
    # divide by log(# of buckets) for normalised entropy value
    Hnorm = - entropy / np.log(len(binCounts)) 
    return Hnorm

def get_normalised_entropy_score(binCounts):
    nm = sum(binCounts) # total number of instances
    
    Hnorm = get_normalised_entropy(binCounts)
    
    # multiply by log(1+total) to reward the number of instances generated
    score = Hnorm * np.log(1+nm)

    return score

# get the diminishing returns coverage score, 
# prioritises coverage but allows for repeated coverage (with diminishing return score rho) to overcome missing bins
def get_frequency_coverage_score(binCounts, rho):
    
    numBuckets = len(binCounts)
    rawScore = 0
    maxCount = max(binCounts)
    
    for k in range(1, maxCount + 1):
        frequencyCount = sum(1 for count in binCounts if count >= k)
        rawScore += pow(base=rho, exp=(k-1)) * frequencyCount
    
    normScore = rawScore / numBuckets
    
    return normScore
    

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

def run_cmd_with_timeout(cmd, printOutput=False, outFile=None, timeout=60):
    lsCmds = shlex.split(cmd)
    try:
        p = subprocess.run(lsCmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", -1
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
