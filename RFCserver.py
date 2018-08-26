#!/usr/bin/env python

"""
ECE 573 Project 1
Venkata Surya Teja Penumatcha
Michael Patel

This is peer RFC server
"""

from socket import *
import random
import json
import threading

# GLOBALs
BUFFER_SIZE = 16384
TIMEOUT = 7200
MAX_NUM_CONN = 20

class RFCserver(object):

    def __init__(self, hostname, portNumber, RFC_index, peerNumber):		
        self.host = hostname
        self.RFCserverportnumber = portNumber
        #self.RFCserverportnumber = random.randint(64500, 65500) # port is specific to peer
        self.serverSocket = socket(AF_INET, SOCK_STREAM) # welcoming socket
        self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.serverSocket.bind((self.host, self.RFCserverportnumber))
        self.RFC_index = RFC_index # create list for peer's RFC index
        self.peerNumber = peerNumber
        self.RFC_index_locks = {}
        self.leave = 0
        # Create a lock for every file
        for item in self.RFC_index:
            self.RFC_index_locks['' + str(item[0]) + '.txt'] = threading.Lock()
        
    def getRFCserverportnumber(self):
        return self.RFCserverportnumber

    def listen(self):
        self.serverSocket.listen(MAX_NUM_CONN)
        print('RFC server ' + str(self.RFCserverportnumber) + ' is listening...')					

        while(self.leave != 1):
            connectionSocket, connectionAddress = self.serverSocket.accept() # welcome socket
            print('\n##########################################')
            print('Connected to ' + str(connectionAddress))
            #connectionSocket.settimeout(TIMEOUT)
            threading.Thread(target = self.listenToClient, args = (connectionSocket, connectionAddress)).start() # spawn new client socket thread
	
    def listenToClient(self, connectionSocket, connectionAddress):
        while(self.leave != 1):
            value = 0
            try:
                request = json.loads(connectionSocket.recv(BUFFER_SIZE)) # socket created specifically for the client (not same as welcoming socket)
                if request:
				    #print("Received from peer: ", request)	# show message the RFC server receives from peer
                    
				    # Peer-to-Peer actions
                    if(request == 'RFCQuery'): # RFC QUERY
                        print('Received RFC Query request\n')
                        response = self.getRFCindex()
                        connectionSocket.send(json.dumps(response).encode()) # send response from RFC server to peer
                        connectionSocket.close()
                        
                    elif(request == 'GetRFC'): # GET RFC part 1
                        print('Received Get RFC request\n')
                        reply = 'Received Get request'
                        connectionSocket.send(json.dumps(reply).encode()) # send reply from RFC server to peer
                        
                    elif(request[0] == 'FileName'): # GET RFC part 2
                        self.getRFC(request[1], connectionSocket, connectionAddress)
                        connectionSocket.close()
                        value = 1
                    else:
                        print('Don\'t recognize request')					
                        
                else:
                    print('\nReceived nothing')
                    raise error('Client disconnected')

            except:
                connectionSocket.close()
			    #return False
            if(value == 1):
                break
	

    def getRFCindex(self): # get RFC index dictionary of peer
        return self.RFC_index

    def mergeRFCindex(self, RFC_index_neighbor):
        self.RFC_index = self.RFC_index + RFC_index_neighbor
        for item in RFC_index_neighbor:
            fileName = '' + str(item[0]) + '.txt'
            if fileName not in self.RFC_index_locks:
                self.RFC_index_locks[fileName] = threading.Lock()
        
    def getRFC(self, fileName, connectionSocket, connectionAddress):
        filepath = 'rfcs' + str(self.peerNumber) + '/'
        
        self.RFC_index_locks[fileName].acquire()
        RFCfile = open(filepath + fileName, 'rb')
        data = RFCfile.read(BUFFER_SIZE)
        while(data):
            connectionSocket.send(data) # not using json.dumps() or encode()
            data = RFCfile.read(BUFFER_SIZE)
        RFCfile.close()
        self.RFC_index_locks[fileName].release()
        
        print(fileName + ' sent\n')
        
    def setLeave(self):
        self.leave = 1
        
