#!/usr/bin/env python
# coding utf-8

import socket, threading,signal,sys



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
			#test
			if int(room)==0:
                                sensor="0"
                                temp=data[2:]
                        else:
                                sensor=data[1]
                                temp=data[3:]
                 	print "client "+ ip+":" +str(port)+" : room "+room+" sensor "+sensor+" temp "+temp  
                        #write temp
                        name="capteur"+room+sensor+".txt"
                        file=open(name,"a")
                        file.write(temp+"\n");
                        file.close()
                        #response
                 	temp.replace(",",".")
                 	temp=float(temp)
                        if int(room)==1:
                                 baseTemp=baseTemp1
                        elif int(room)==2:
                                 baseTemp=baseTemp2
                        if temp<baseTemp:
                                resp="1 "+str(baseTemp-temp) #1=up
                                self.socket.send(resp)
                        if temp>baseTemp:
                                resp="2 "+str(temp-baseTemp)#2=down
                                self.socket.send(resp)self.sendResp(int(room),float(temp))       
                print " Client disconnected"       
                self.socket.close()        
                        

def signal_handler(signal,frame):
	print "Close"
	serverSocket.close()
	for i in threads:
		i.stop()
	sys.exit(0)



def setBaseTemp(newTemp,salle):
       if salle==1:
               baseTemp1=newTemp
       elif salle==2:
               baseTemp2=newTemp


signal.signal(signal.SIGINT,signal_handler)
serverPort = 4242 

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
serverSocket.bind(('',serverPort))

baseTemp1= setBaseTemp(30,1)
baseTemp2= setBaseTemp(28,2)


threads=[] 

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

