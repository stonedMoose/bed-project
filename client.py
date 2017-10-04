#!/usr/bin/env python
# coding: utf-8

import socket,signal,sys,threading

host=''
downStreamPort = 5555
upStreamPort = 4242
slaveId = 1
stopped=False
ip='172.20.10.10'

def signal_handler(signal,frame) :
	print('End')
	t1.stop()
	stopped=True
	s.close()
	sys.exit(0)

class UpStream(threading.Thread) :
	def __init__(self,s,qUp):
		threading.Thread.__init__(self)
		self.s=s
		self.q=qUp
		self.__stop__event=threading.Event()
	def stop(self) :
		self.__stop__event.set()
	def stopped(self) :
		return self.__stop__event.is_set()
	def run(self) :
		print('Connection on '+format(upStreamPort))
		while self.stopped()!=True :
			#get data from queue
			if self.q.empty()!=True :
				#parse data
				data=self.q.get()
				#data=raw_input('Data to send : ')
				if len(data)>0 :
					self.s.send(data['id']+' '+data['temperature']+'|')
					print('Sending : '+str(data)+'\r')
				else :
					self.stop()
		print('T1 : Close')
		#self.s.close()


def gateway(qUp,qDown) :
	signal.signal(signal.SIGINT,signal_handler)
	#host = raw_input('@IP of the MasterPi : ') # @IP of MasterPi
	#if len(host)==0 :
	host=ip
	print('host : ' + host)
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
	s.bind(('',5555))
	s.connect((host, upStreamPort))

	#starts the queue reading + temp forwarding
	t1=UpStream(s,qUp)
	t1.start()

	while stopped==False :
		command=s.recv(255)
		if len(command)>0 :
			#parse the command : check if the command is for our network, then send it on the uart
			print('command : '+command+'\r')
			qDown.put(command[0]+' '+command[2:])
			#toTransmit = slaveId*10 +' '
		else :
			print('Error in message')
			stop()

	t1.join()
	print('Out of loop')
	s.close()

