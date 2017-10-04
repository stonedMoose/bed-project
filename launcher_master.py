#!/usr/bin/python
from multiprocessing import Process, Queue
# import here the function reading serial and the one sending data through wifi #
from server import main
from gui import main_gui
from signal import signal, SIGINT


global gui_process, server_process


def interrupt():
    gui_process.terminate()
    server_process.terminate()

signal(SIGINT, interrupt)

# cree une queue de taille 10
q = Queue(10)

gui_process = Process(target=main_gui, args=(q,))
gui_process.daemon = True
gui_process.start()        # Launch reader() as a separate python process

server_process = Process(target=server_process, args=(q,))
server_process.daemon = True
server_process.start()

# wait for parser process to end
gui_process.join()
