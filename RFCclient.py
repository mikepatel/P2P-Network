#!/usr/bin/env python

"""
ECE 573 Project 1
Venkata Surya Teja Penumatcha
Michael Patel

This is peer RFC client
"""

# RFC client

"""
- connection w/ RS
- client cookie token
- request RFC index to another peer
- merge new RFC index w/ existing RFC index
- then search RFC index
- connect to RFC server of peer with RFC index

functions:
- register() = peer opens TCP connection to send registration message to RS, and provide info about the port to which its RFC server listens
- leave() = peer opens TCP connection to send message to RS
- pquery() = peer opens TCP connection to send query message to RS, receives active peer list in response
- keepalive() = peer sends message to RS to let it know it is still alive (TTL for this peer is reset to 7200)

- rfcquery() = peer requests RFC index from another peer
- getRFC() = peer requests to download specific RFC document from another peer

- Open and close new TCP connection for each message, whether peer-to-RS or peer-to-peer
"""

from socket import *
import json
import threading
import platform

# GLOBALs
RSservername = 'localhost'
RSserverport = 65423
BUFFER_SIZE = 16384
NOT_REGISTERED = -1

#
class RFCclient(object):
	#
    def __init__(self, RFCserverportnumber): # RFC server port number is passed in from parent (peer)
        self.peerRecord = {}
        self.RFCserverportnumber = RFCserverportnumber
        self.cookie = NOT_REGISTERED
        self.message = ''
        self.response = ''
        self.activePeerList = {}

    def register(self):
        # open TCP connection and provide REGISTRATION message to RS
        clientSocket = self.openConnection(RSservername, RSserverport)
        self.peerRecord.update({'type' : 'REG', 'cookie' : self.cookie, 'portNumber' : self.RFCserverportnumber})
        self.sendMessage(clientSocket, self.peerRecord)

        # receive and update cookie information
        self.cookie = self.getResponse(clientSocket)
        self.peerRecord.update({'cookie' : self.cookie})
		
        # close TCP connection
        self.closeConnection(clientSocket)
        #print('\nregister')
        #print(self.peerRecord)

    def leave(self):
        # open TCP connection and provide LEAVE message to RS
        clientSocket = self.openConnection(RSservername, RSserverport)
        self.peerRecord.update({'type' : 'LEAVE', 'cookie' : self.cookie, 'portNumber' : self.RFCserverportnumber})
        self.sendMessage(clientSocket, self.peerRecord)

        # close TCP connection
        self.closeConnection(clientSocket)
        #print('\nleave')
        #print(self.peerRecord)

    def pquery(self):
        # open TCP connection and provide PQUERY message to RS
        clientSocket = self.openConnection(RSservername, RSserverport)
        self.peerRecord.update({'type' : 'QUERY', 'cookie' : self.cookie, 'portNumber' : self.RFCserverportnumber})
        self.sendMessage(clientSocket, self.peerRecord)

        # receive and update list of active peers
        self.response = self.getResponse(clientSocket)
        self.activePeerList.update(self.response)
		
        # close TCP connection
        self.closeConnection(clientSocket)
        #print('\npquery')
        #print(self.activePeerList)
        return self.activePeerList

    def keepAlive(self):
        threading.Timer(5000, self.keepAlive).start() # periodically call keepAlive()

        # open TCP connection and provide KEEP ALIVE message to RS
        clientSocket = self.openConnection(RSservername, RSserverport)
        self.peerRecord.update({'type' : 'ALIVE', 'cookie' : self.cookie, 'portNumber' : self.RFCserverportnumber})
        self.sendMessage(clientSocket, self.peerRecord)

        # close TCP connection
        self.closeConnection(clientSocket)
        #print('\nkeep alive')

    def rfcquery(self, serverName, serverPort): # peer requests RFC index from remote peer
        print("\n--------------------")
        print("\nGET RFC-Index P2P-DI/1.0")
        print("HOST: " + gethostname())
        print("OS: " + str(platform.system()) + " " + str(platform.release()))
        # open TCP connection and provide RFC QUERY message to peer
        clientSocket = self.openConnection(serverName, serverPort) 
        self.sendMessage(clientSocket, 'RFCQuery')

        # receive other peer's RFC index, Buffer size multiplied by 10 for more than 60 RFCs
        RFC_index = json.loads(clientSocket.recv(BUFFER_SIZE*2))

        # close TCP connection
        self.closeConnection(clientSocket)
        return RFC_index

    def getrfc(self, entry, serverName, serverPort, peerNumber): # peer requests to download a specific RFC document from remote peer
        print('\n--------------------')
        print('\nGET RFC ' + str(entry[0]))
        print('HOST: ' + gethostname())
        print('OS: ' + str(platform.system()) + ' ' + str(platform.release()))
        fileName = str(entry[0]) + '.txt'

        # open TCP connection and provide GET RFC message to peer
        clientSocket = self.openConnection(serverName, serverPort)
        self.sendMessage(clientSocket, 'GetRFC')

		# peer's RFC server sends a reply implying that we should send filename
        reply = self.getResponse(clientSocket)
        message = ['FileName', fileName]
        self.sendMessage(clientSocket, message)

        # receive RFC document from other peer
        with open('rfcs' + str(peerNumber) + '/' + fileName, 'wb') as RFCfile:
            while True:
                data = clientSocket.recv(BUFFER_SIZE) # not using json.loads() or decode()
                if not data:
                    break
                RFCfile.write(data)
        RFCfile.close()

        # close TCP connection
        self.closeConnection(clientSocket)

    def openConnection(self, host, port):
        clientSocket = socket(AF_INET, SOCK_STREAM) # IPv4, TCP
        clientSocket.connect((host, port))
        return clientSocket

    def closeConnection(self, clientSocket):
        clientSocket.close()

    def sendMessage(self, clientSocket, message):
        clientSocket.send(json.dumps(message).encode())

    def getResponse(self, clientSocket):
        return json.loads(clientSocket.recv(BUFFER_SIZE))
