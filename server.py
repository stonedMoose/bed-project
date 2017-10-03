#!/usr/bin/env python
# coding utf-8

import socket, threading,signal,sys

def signal_handler(signal,frame):
	print "Close"
	serverSocket.close()
	for i in threads:
		i.stop()
	sys.exit(0)



#def changetemp(signal,frame):


signal.signal(signal.SIGINT,signal_handler)
#signal.signal(signal.SIGQUIT,changetemp)	
serverPort = 4242 

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
serverSocket.bind(('',serverPort))
baseTemp= float(raw_input("Please enter the temperature you wish in the room\n"))
print("you want "+str(baseTemp)+" degree")


threads=[]

class ClientHandler(threading.Thread):
        def __init__(self,ip,port,socket):
                threading.Thread.__init__(self)
                self.ip=ip
                self.port=port
                self.socket=socket
                print " [+] New thread started for client "+ip+" : "+str(port)
		self.__stop__event=threading.Event()

	def stop(self):
		self.__stop__event.set()

	def stopped(self):
		return self.__stop__event.is_set()


        def run(self):
                print "\n Connection from : "+ip+" : "+str(port)+" with socket"+str(self.socket.getsockname())
                data="dump"
                while self.stopped()!=True:
                        data=self.socket.recv(255)
			if not data:
				self.stop()
				break
			room=data[0]
			sensor=data[1]
			temp=(float(data[3:])/10.0)
                 	print "client "+ ip+":" +str(port)+" : room "+room+" sensor "+sensor+" temp "+str(temp)  
			if temp<baseTemp:
				resp="1 "+str(baseTemp-temp) #1=up
				self.socket.send(resp)
			if temp>baseTemp:
				resp="2 "+str(temp-baseTemp)#2=down
				self.socket.send(resp)
                print " Client disconnected"       
                self.socket.close()        
                        
   

while True :
	try:
		serverSocket.listen(5)
		print "\n Listening for incoming connections..."
	      	(clientSocket, (ip,port))=serverSocket.accept()
		newClientHandlerThread=ClientHandler(ip,port,clientSocket)
		newClientHandlerThread.start()
		newClientHandlerThread.join()
		threads.append(newClientHandlerThread)
	except KeyboardInterrupt:
		baseTemp=raw_input("Please entre the new temperature you wish in the room\n")
		print("you want "+baseTemp+" degree")
