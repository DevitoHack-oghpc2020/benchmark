"""
Run benchmarks for all participants.
"""

import os
import urllib.request
import json
import re
import subprocess
from shutil import copy
from tempfile import gettempdir
from utils import generate_score_html
from memoization import cached

# Detect (or create) Devito JIT cache dir
def get_jitcachedir():
    tempdir = gettempdir()
    jitcachedir = [i for i in os.listdir(
        tempdir) if i.startswith('devito-jitcache')]
    if len(jitcachedir) == 0:
        # Create JITcache dir as Devito would normally do
        jitcachedir = os.path.join(tempdir, 'devito-jitcache-uid%s' % os.getuid())
        os.makedirs(jitcachedir, exist_ok=True)
    elif len(jitcachedir) == 1:
        jitcachedir = os.path.join(tempdir, jitcachedir.pop())
    else:
        raise ValueError("Multiple JIT cache dirs found ?")
    print("jitcache dir =", jitcachedir)
    return jitcachedir

# Get a dict of all forks {username:repo}
def get_forks():
    origin = "https://github.com/DevitoHack-oghpc2020/starter"
    user = "DevitoHack-oghpc2020"
    repo = "starter"
    users = []

    github_url = 'https://api.github.com/repos/%s/%s/forks'
    resp = urllib.request.urlopen(github_url % (user, repo))
    if resp.code == 200:
        content = resp.read()
        data = json.loads(content)
        for remote in data:
            users.append(remote["owner"]["login"])

    print("users = ", users)

    forks = {"devito": "%s.git" % origin}
    for user in users:
        forks[user] = "https://github.com/%s/starter.git" % user

    return forks

def publish_results(mapper):
    if not os.path.isdir("DevitoHack-oghpc2020.github.io"):
        subprocess.call(
            "git clone https://github.com/DevitoHack-oghpc2020/DevitoHack-oghpc2020.github.io.git".split())

    os.chdir("DevitoHack-oghpc2020.github.io")
    subprocess.call("git pull origin master".split())

    os.chdir("../")
    generate_score_html(mapper)
    os.chdir("DevitoHack-oghpc2020.github.io")

    subprocess.call("git add index.html".split())
    subprocess.call("git commit -m \"update\"".split())
    subprocess.call("git push".split())
    os.chdir("../") 

    return

def update_fork(user, repo):
   # Clone fork
    if not os.path.isdir(user):
        clone_cmd = "git clone %s %s" % (repo, user)
        subprocess.call(clone_cmd.split())

    os.chdir(user)

    # Update fork
    subprocess.call("git pull".split())

    output = subprocess.run("git rev-parse --verify HEAD".split(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commit_hash = output.stdout.decode("utf-8").strip()
    os.chdir("../")

    return commit_hash

@cached
def benchmark(commit_hash, user, mapper):
    print("*** Benchmarking user `%s` " % user, commit_hash)

    os.chdir(user)

    # Reset environment
    found = [i for i in os.environ if i.startswith('DEVITO_')]
    for i in found:
        del os.environ[i]

    if not os.path.exists('env.py'):
        print("Couldn't find `env.py`, skipping `%s` ..." % user)
        os.chdir("../")
        return

    # Set environment based on the fork's env.sh
    environ = eval(open("env.py").read())
    for k, v in environ.items():
        os.environ[k] = v
    os.environ['DEVITO_LOGGING'] = 'PERF'  # Enforce log level
    for k, v in os.environ.items():
        if k.startswith('DEVITO_'):
            print("%s=%s" % (k, v))

    # Populate JIT-cache
    for i in os.listdir('edited-files'):
        fromfile = os.path.join(jitcachedir, i)
        copy(os.path.join('edited-files', i), jitcachedir)

    # Run experiments
    mapper[user] = {}
    for problem in ['acoustic', 'tti']:
        # Populate with dummy values
        mapper[user][problem] = {
            'time': 0,  # Runtime in seconds
            'perf': 0,  # Performance in GPoints/s
            'err': {}
        }

        result = subprocess.run(['python', 'run-preset.py', problem],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stderr.decode("utf-8").split('\n')

        # Horrible, but it should do what we need
        try:
            for i in output:
                if i.startswith('Operator `Forward` run') or i.startswith('Operator `ForwardTTI` run'):
                    mapper[user][problem]['time'] = float(i.split()[4])
                if 'FD-GPts/s' in i:
                    mapper[user][problem]['perf'] = float(i.split()[2])
                if i.startswith('norm'):
                    err = mapper[user][problem]['err']
                    fname = re.search(r'\((.*?)\)', i).group(1)
                    computed, expected, delta = re.findall(
                        r"[-+]?\d*\.\d+|\d+", i)
                    err[fname] = (float(computed), float(
                        expected), float(delta))
        except:
            # Hopefully we only end up here because the benchmark was never run by the fork
            pass

    os.chdir("../")

jitcachedir = get_jitcachedir()
mapper = {}

# Run benchmarks
while True:
    forks = get_forks()

    for user in forks:
        commit_hash = update_fork(user, forks[user])
        benchmark(commit_hash, user, mapper)

    publish_results(mapper)