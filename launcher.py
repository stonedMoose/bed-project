#!/usr/bin/python
from multiprocessing import Process, Queue
# import here the function reading serial and the one sending data through wifi #
from parse_serial import parse


def reader(queue):
    while True:
        if not queue.empty():
            print q.get(), "\r"

# cree une queue de taille 10
q = Queue(10)

parser_process = Process(target=parse, args=(q,))
parser_process.daemon = True
parser_process.start()        # Launch reader() as a separate python process

# sender_process = Process(target=reader, args=(q,))
# sender_process.daemon = True
# sender_process.start()

# wait for parser process to end
parser_process.join()
