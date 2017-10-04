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

        def writeTempFile(self,room,sensor,temp):
                name="capteur"+room+sensor+".txt"
                file=open(name,"a")
                file.write(str(temp)+"\n");
                file.close()

        def sendResp(self,room,temp):
                global baseTemp1
                global baseTemp2
                if room==1:
                          baseTemp=baseTemp1
                elif room==2:
                          baseTemp=baseTemp2
                print "baseTemp :"+str(baseTemp)+" room:"+str(room)
                if temp<baseTemp:
                          resp="1 "+str(baseTemp-temp)+"|" #1=up
                          self.socket.send(resp)
                if temp>baseTemp:
                          resp="2 "+str(temp-baseTemp)+"|" #2=down
                          self.socket.send(resp)     
                print "sending back to "+self.ip+":"+resp

        def showBaseTemp(self):
                global baseTemp1
                global baseTemp2
                print self.ip+": bt1:"+str(baseTemp1)+" bt2:"+str(baseTemp2)+"\n"

                
        def run(self):
                print "\n Connection from : "+self.ip+" : "+str(self.port)+" with socket"+str(self.socket.getsockname())+"\n"
                data="dump"
                while self.stopped()!=True:
                        data=self.socket.recv(255)
			if not data:
				self.stop()
				break
			print "data received"+data+"\n"
			dataList=data.split('|')
			for item in dataList:
                                if item:
                                        room=item[0]
                                        #test
                                        sensor=item[1]
                                        temp=item[3:]
                                        print "\n client "+ self.ip+":" +str(self.port)+" : room "+room+" sensor "+sensor+" temp "+temp
                                        temp=temp.replace(",",".")
                                        temp=float(temp)
                                        #write temp
                                        self.writeTempFile(room,sensor,temp)
                                        #response
                                        self.sendResp(int(room),temp)
                print " Client disconnected"       
                self.socket.close()        
                        

def signal_handler(signal,frame):
        global serverSocket,threads
	print "Close"
	serverSocket.close()
	for i in threads:
		i.stop()
	sys.exit(0)



def setBaseTemp(newTemp,salle):
       global baseTemp1
       global baseTemp2
       global threads
       print "newTemp: ", newTemp,"room", salle
       if salle==1:
               baseTemp1=newTemp
       elif salle==2:
               baseTemp2=newTemp
       try:
               for t in threads:
                      t.showBaseTemp()
       except NameError:
               pass

def main():
        
        signal.signal(signal.SIGINT,signal_handler)
        serverPort = 4242

        global serverSocket,threads

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        serverSocket.bind(('',serverPort))

        global baseTemp1,baseTemp2
        baseTemp1=0
        baseTemp2=0

        setBaseTemp(30,1)
        setBaseTemp(28,2)
        print "room1: "+str(baseTemp1) +" room2 : "+str(baseTemp2)


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
                        threads[-1].showBaseTemp() 
                except KeyboardInterrupt:
                        baseTemp=raw_input("Please entre the new temperature you wish in the room\n")
                        print("you want "+baseTemp+" degree")

#if __name__ == '__main__':
main()
