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

import os
import urllib.request
import json
import subprocess

origin = "https://github.com/DevitoHack-oghpc2020/starter"
user = "DevitoHack-oghpc2020"
repo = "starter"
forks = []

github_url='https://api.github.com/repos/%s/%s/forks'
resp = urllib.request.urlopen(github_url % (user, repo))
if resp.code == 200:
    content = resp.read()
    data = json.loads(content)
    for remote in data:
        forks.append(remote["owner"]["login"])

print("forks = ", forks)

repos = {"devito":"%s.git"%origin}
for fork in forks:
    repos[fork] = "https://github.com/%s/starter.git"%fork

for fork in repos:
    if not os.path.isdir(repo):
        clone_cmd = "git clone %s %s"%(repos[fork], fork)
        subprocess.call(clone_cmd.split())
    os.chdir(fork)
    subprocess.call("git pull".split())

    # what commands to run to evaluate the benchmarks with the pushed manually updated code?
    # parse output, collect results

    os.chdir("../")

print(repos)
#         origin = subprocess.check_output(origin_cmd).strip()
