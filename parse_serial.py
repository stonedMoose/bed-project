#!/usr/bin/python
import subprocess
import re
import os
import json
import platform
from multiprocessing import Queue

# h1 rsp 1
# h2 rsp 2
# 11, 12 salle 1
# 21, 22 salle 2


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def parse(queue):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if platform.architecture() == ('32bit', 'ELF'):
        bin_path = os.path.join(dir_path, "ezconsole", "ezconsole_bin_raspberry")
    else:
        bin_path = os.path.join(dir_path, "ezconsole", "ezconsole")
    for line in execute(bin_path):
        if "temperature" in line:
            try:
                # print(line)
                values = json.loads(line)
                queue.put(values)
            except ValueError:
                pass

