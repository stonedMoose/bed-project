#!/usr/bin/python
from multiprocessing import Process, Queue
# import here the function reading serial and the one sending data through wifi #
from parse_serial import parse
from client import gateway
from signal import signal, SIGINT


global parser_process, gw_process


def interrupt():
    parser_process.terminate()
    gw_process.terminate()

signal(SIGINT, interrupt)

# cree une queue de taille 10
q = Queue(10)
q2 = Queue(10)

parser_process = Process(target=parse, args=(q, 1,))
parser_process.daemon = True
parser_process.start()        # Launch reader() as a separate python process

gw_process = Process(target=gateway, args=(q,q2,))
gw_process.daemon = True
gw_process.start()

# wait for parser process to end
parser_process.join()
