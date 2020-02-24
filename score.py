"""
Run benchmarks for all participants.
"""

import glob
import os
import subprocess
from shutil import copyfile, copytree, rmtree

def benchmark_this(submission, cmd):
    cwd = os.getcwd() 
    os.chdir(submission)

    score = None

    try:
        # Run benchmark - a list of the commandline, e.g. python hello_world.py
        output = subprocess.check_output(cmd).splitlines()

        # Parse output to get performance metric
        output.reverse()
        for line in output:
            line = line.decode('ascii')
            if "GPts/s" in line:
                _, _score = line.split(":")
                score = float(_score)
                break
    except:
        pass

    os.chdir(cwd)
    return score

def score(submission):
    scores = []
    scores.append(benchmark_this(submission, ["echo", "GPts/s : 1e+12"]))

    return scores

assignment = "/tmp/oghpc-02-24-2020-12-28-32"

os.chdir(assignment)

submissions = glob.glob("*")

scores = {}
for submission in submissions:
    scores[submission] = score(submission)

print(scores)
