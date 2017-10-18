# Created by  Lisa Martini on 10/18/2017


#!/usr/bin/python
from multiprocessing import Process, Queue
from signal import signal, SIGINT
import subprocess
import re
import os, sys
import json
import platform
import threading
import pymongo
import datetime
from pymongo import MongoClient


global parser_process


def interrupt():
    parser_process.stop()
    sys.exit(0)


class ParserProcess(threading.Thread):
    def __init__(self ):
        threading.Thread.__init__(self)
        self.client = MongoClient()
        self.db = self.client.residenceA #one database for each residency
        self.room = self.db.temperatures # for now on only one collection called temperatures
        print(self.db)
        print(self.room)
        self.__stop__event = threading.Event()

    def stop(self):
        self.__stop__event.set()
        self.client.close()

    def stopped(self):
        return self.__stop__event.is_set()

    def execute(self, cmd):
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    def run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if platform.architecture() == ('32bit', 'ELF'):
            bin_path = os.path.join(dir_path, "ezconsole", "ezconsole_bin_raspberry")
        else:
            bin_path = os.path.join(dir_path, "ezconsole", "ezconsole")

        for line in self.execute(bin_path):
            #print(line)
            id = "10"
            if "id" in line:
                values = json.loads(line)
                id = values["id"]
                #print(id)
            if "temperature" and "time" in line:
                values = json.loads(line)
                temp = values["temperature"]
                date = values["time"]
                doc ={"sensorId": id, "date": date, "temperature": temp}
                #print(doc)
                doc_id = self.room.insert_one(doc).inserted_id
                #print(doc_id)


signal(SIGINT, interrupt)
parser_process = ParserProcess()
parser_process.start()
parser_process.join()