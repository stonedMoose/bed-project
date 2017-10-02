#!/usr/bin/python3
'''
import subprocess
import re

def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

for path in execute(["/home/fphan/5TC/BED/TP/Projet/ezconsole", ""]):
	if "temperature: " in path:
		lst = re.findall(r"[\w']+", path)
		print(lst[1])
'''

import subprocess
import re
import os

def execute(cmd):
	popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
	for stdout_line in iter(popen.stdout.readline, ""):
		yield stdout_line
	popen.stdout.close()
	return_code = popen.wait()
	if return_code:
		raise subprocess.CalledProcessError(return_code, cmd)

def display():
	dir_path = os.path.dirname(os.path.realpath(__file__))
	dir_path = dir_path + "/ezconsole"
	for path in execute(dir_path):
		if "temperature: " in path:
			lst = re.findall(r"[\w']+", path)
			print(lst)

display()
