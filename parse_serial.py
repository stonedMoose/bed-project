#!/usr/bin/python3
import subprocess
import re
import os
import json


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
    bin_path = os.path.join(dir_path, "ezconsole", "ezconsole")
    for line in execute(bin_path):
            # values = json.load(line)
            # print(values)
            # queue.put(values)
            lst = re.findall(r"[\w']+", line)
            print(lst)

parse(1)
