#!/usr/bin/env python

"""
ECE 573 Project 1
Venkata Surya Teja Penumatcha
Michael Patel

This is Registration Server (RS)
"""

# Registration Server
"""
RS has a well-known port number known to all peers
	- port number = 65423

Keeps information on active peers, but not the information peers have about their RFCs

fields handled from peer:
- cookie # cookie assigned to peer as type integer
- port number # port number of peer's RFC server as type integer (valid only if peer is active)

fields hanlded by RS:
- hostname # hostname of peer as type string
- status # flag to indicate whether peer is currently active as type Boolean
- TTL # type integer
- numActive # number of times peer has been active in last 30 days as type integer
- timestamp # most recent date/time peer has registered
"""

from socket import *
import threading
import json
import datetime

# GLOBALs
MAX_NUM_CONN = 20
TIMEOUT = 7200
BUFFER_SIZE = 16384
NOT_REGISTERED = -1
ACTIVE = True
INACTIVE = False

#
class RegistrationServer(object):

	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.serverSocket = socket(AF_INET, SOCK_STREAM) # welcoming socket
		self.serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.serverSocket.bind((self.host, self.port))
		self.cookieCounter = 0
		self.PeerDict = {}
		self.tempIdentifier = 0	
		
	def listen(self):
		self.serverSocket.listen(MAX_NUM_CONN)
		#print("\nHost is ", self.host)
		print('RS is listening...')					

		while True:
			connectionSocket, connectionAddress = self.serverSocket.accept()
			print('\n##########################################')
			print('Connected to ' + str(connectionAddress))
			connectionSocket.settimeout(TIMEOUT)
			threading.Thread(target = self.listenToClient, args = (connectionSocket, connectionAddress)).start()			

	def listenToClient(self, connectionSocket, connectionAddress):
		while True:
			try:
				# Handshaking completes between clientSocket (client) and connectionSocket (server)
				data = json.loads(connectionSocket.recv(BUFFER_SIZE)) # socket created specifically for the client (not same as welcoming socket)
				if data:			
					#print("Received from peer: ", data)	# show message the RS receives from peer
					
					messageType = data['type'] # get message type
					identifier = data['cookie'] # identifier = cookie integer unique to each peer

					# extract message parameters from client
					tempHostname = connectionAddress[0] # IP address
					tempCookie = data['cookie']	# cookie integer unique to each peer
					tempStatus = ACTIVE # reset status value to Active (true) b/c peer contacted RS
					tempTTL = TIMEOUT # reset Timeout value to 7200 b/c peer contacted RS
					tempPortnumber = data['portNumber']	# peer's RFC server port number (Not port number of TCP connection)	
					if(messageType == 'REG'): # identifier not yet set
						tempNumActive = 0
						tempTimestamp = ''	# timestamp of most recent time peer registered
					else:
						tempNumActive = self.getNumActive(identifier) # only needed when performing the registration of a peer
						tempTimestamp = self.getTimestamp(identifier)					

					# Peer-To-RS actions
					if(messageType == 'REG'): # Registration actions
						#print('begin reg')
						print('\nReceived REGISTRATION message')
						self.performRegistration(identifier, tempHostname, tempCookie, tempStatus, tempTTL, tempPortnumber, tempNumActive, tempTimestamp)
						identifier = self.tempIdentifier # update identifier
						response = self.getCookie(identifier) # return cookie information to peer
						#print('end reg')						

					elif(messageType == 'LEAVE'): # Leave actions
						#print('begin leave')
						print('\nReceived LEAVE message')
						tempStatus = INACTIVE # set status field to Inactive (false) for when peer wants to leave
						self.updatePeerRecord(identifier, tempHostname, tempCookie, tempStatus, tempTTL, tempPortnumber, tempNumActive, tempTimestamp) # update status field
						#print(self.getStatus(identifier))
						#print('end leave')

					elif(messageType == 'QUERY'): # Peer Query actions
						#print('begin query')
						print('\nReceived PQUERY message')
						response = self.getActivePeerList() # return active peer list to peer
						#print(response)
						#print('end query')

					elif(messageType == 'ALIVE'): # Keep Alive actions
						#print('begin alive')
						print('\nReceived KEEP ALIVE message')
						tempTTL = TIMEOUT # reset TTL field to 7200 for when peer contacts RS
						self.updatePeerRecord(identifier, tempHostname, tempCookie, tempStatus, tempTTL, tempPortnumber, tempNumActive, tempTimestamp) # update TTL field
						#print('end alive')

					else:
						response ='ERROR'

					connectionSocket.send(json.dumps(response).encode()) # send response from RS to peer

				else:
					raise error('Client disconnected')

			except:
				connectionSocket.close()
				#return False

	def performRegistration(self, identifier, hostname, cookie, status, TTL, portNumber, numActive, timestamp):
		if(cookie == NOT_REGISTERED): # check if peer is registered
			cookie = self.createCookie()
			self.tempIdentifier = cookie # update Global identifier variable
			identifier = self.tempIdentifier # update local identifier variable
		numActive =+ 1 # number of times this peer has been active (i.e. has registered) in last 30 days
		timestamp = str(datetime.datetime.now()) # timestamp of most recent time peer registered
		self.updatePeerRecord(identifier, hostname, cookie, status, TTL, portNumber, numActive, timestamp) # update cookie, numActive and timestamp fields

	def createCookie(self):
		self.cookieCounter += 1
		return self.cookieCounter

	def getHostname(self, identifier):
		return self.PeerDict[identifier]['hostname']

	def getCookie(self, identifier):
		return self.PeerDict[identifier]['cookie']

	def getStatus(self, identifier):
		return self.PeerDict[identifier]['status']

	def getTTL(self, identifier):
		return self.PeerDict[identifier]['TTL']

	def getPortnumber(self, identifier):
		return self.PeerDict[identifier]['portNumber']

	def getNumActive(self, identifier):
		return self.PeerDict[identifier]['numActive']

	def getTimestamp(self, identifier):
		return self.PeerDict[identifier]['timestamp']

	def getActivePeerList(self):
		tempDict = {}
		for key in self.PeerDict:
			if(self.getStatus(key) == ACTIVE): # check if peer's status is Active
				tempDict.update({key : self.PeerDict[key]})
		#print('\nActive Peer List', tempDict)
		if(len(tempDict) == 0): # there are no active peers
			return 'NO ACTIVE PEERS'
		else:
			return tempDict

	def updatePeerRecord(self, identifier, hostname, cookie, status, TTL, portNumber, numActive, timestamp):
		self.PeerDict.update({identifier : {'hostname' : hostname, 'cookie' : cookie, 'status' : status, 'TTL' : TTL, 'portNumber' : portNumber, 'numActive' : numActive, 'timestamp' : timestamp}})

	def decrementTTL(self): # gets called every 10 seconds	
		threading.Timer(10, self.decrementTTL).start()	
		
		for key in self.PeerDict: # decrement TTL for every peer
			TTL = self.getTTL(key) - 10 # decrement each peer's TTL by 10
			if(TTL == 0): # TTL for peer has expired
				status = INACTIVE
			else: 
				status = ACTIVE
			#print('key', key, 'TTL', TTL)

			# unchanged fields in peer record
			hostname = self.getHostname(key)
			cookie = self.getCookie(key)
			portNumber = self.getPortnumber(key)
			numActive = self.getNumActive(key)
			timestamp = self.getTimestamp(key)
			self.updatePeerRecord(key, hostname, cookie, status, TTL, portNumber, numActive, timestamp) # update status and TTL fields


##########
HOST = ''
RSserverPort = 65423 # universal port number known to all peers
rs = RegistrationServer(HOST, RSserverPort)
rs.decrementTTL() # 1s timer for TTL fields
rs.listen()

