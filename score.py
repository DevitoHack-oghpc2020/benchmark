"""
Run benchmarks for all participants.
"""

import os
import subprocess
import urllib.request
import json
import re
import subprocess
from shutil import copy
from tempfile import gettempdir


# Detect (or create) Devito JIT cache dir
tempdir = gettempdir()
jitcachedir = [i for i in os.listdir(tempdir) if i.startswith('devito-jitcache')]
if len(jitcachedir) == 0:
    # Create JITcache dir as Devito would normally do
    jitcachedir = os.path.join(tempdir, 'devito-jitcache-uid%s' % os.getuid())
    os.makedirs(jitcachedir, exist_ok=True)
elif len(jitcachedir) == 1:
    jitcachedir = os.path.join(tempdir, jitcachedir.pop())
else:
    raise ValueError("Multiple JIT cache dirs found ?")
print("jitcache dir =", jitcachedir)


# Detect all forks
origin = "https://github.com/DevitoHack-oghpc2020/starter"
user = "DevitoHack-oghpc2020"
repo = "starter"
forks = []

github_url = 'https://api.github.com/repos/%s/%s/forks'
resp = urllib.request.urlopen(github_url % (user, repo))
if resp.code == 200:
    content = resp.read()
    data = json.loads(content)
    for remote in data:
        forks.append(remote["owner"]["login"])

print("forks = ", forks)

repos = {"devito": "%s.git" % origin}
for fork in forks:
    repos[fork] = "https://github.com/%s/starter.git" % fork

# Run benchmarks
mapper = {}
for fork in repos:
    print("*** Benchmarking user `%s` ***" % fork)

    # Clone fork
    if not os.path.isdir(fork):
        clone_cmd = "git clone %s %s"%(repos[fork], fork)
        subprocess.call(clone_cmd.split())

    os.chdir(fork)

    # Update fork
    subprocess.call("git pull".split())

    # Reset environment
    found = [i for i in os.environ if i.startswith('DEVITO_')]
    for i in found:
        del os.environ[i]

    if not os.path.exists('env.py'):
        print("Couldn't find `env.py`, skipping `%s` ..." % fork)
        os.chdir("../")
        continue

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
    mapper[fork] = {}
    for problem in ['acoustic', 'tti']:
        # Populate with dummy values
        mapper[fork][problem] = {
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
                    mapper[fork][problem]['time'] = float(i.split()[4])
                if 'FD-GPts/s' in i:
                    mapper[fork][problem]['perf'] = float(i.split()[2])
                if i.startswith('norm'):
                    err = mapper[fork][problem]['err']
                    fname = re.search(r'\((.*?)\)', i).group(1)
                    computed, expected, delta = re.findall(r"[-+]?\d*\.\d+|\d+", i)
                    err[fname] = (float(computed), float(expected), float(delta))
        except:
            # Hopefully we only end up here because the benchmark was never run by the fork
            pass

    os.chdir("../")


if not os.path.isdir("DevitoHack-oghpc2020.github.io"):
    subprocess.call("git clone https://github.com/DevitoHack-oghpc2020/DevitoHack-oghpc2020.github.io.git".split())

os.chdir("DevitoHack-oghpc2020.github.io")
subprocess.call("git pull origin master")

# <Vitor's stuff to go here>
html = open("index.html")
html.write("""<html>
  <head>
    <title>Hackathon league tabke</title>
  </head>
  <body>
      WIP for https://github.com/DevitoHack-oghpc2020/starter
      <table style="width:100%">
""")
for fork in mapper:
    html.write("<tr><th>%s</th><th>%.1f GPts/s</th><th>%.1f GPts/s</th></tr>"%(fork, mappers[fork]["acoustic"]["perf"], mappers[fork]["tti"]["perf"]))
html.write(""" </body>
</html>
""")
html.close()
# </Vitors stuff>

subprocess.call("git add index.html".split())
subprocess.call("git commit -m \"update\"".split())
subprocess.call("git push".split())




