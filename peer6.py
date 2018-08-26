#!/usr/bin/env python

"""
ECE 573 Project 1
Venkata Surya Teja Penumatcha
Michael Patel

This is Peer 6
"""

# Peer 6

"""
RFC_number as integer
RFC_title as string
hostname = of peer containing RFC as string
TTL = local RFCs stays at 7200 (never modified), remote RFCs decremented as integer
"""

from socket import *
import os
import threading
from time import sleep
import random
from datetime import datetime
from RFCclient import RFCclient
from RFCserver import RFCserver

# GLOBALs
RSservername = 'localhost'
RSserverport = 65423 # known to all peers
BUFFER_SIZE = 16384
TIMEOUT = 7200

#
peerNumber = 6 # ONLY MAJOR DIFFERNCE ACROSS DIFFERENT PEER FILES
hostName = 'localhost'
portNumber = random.randint(64500, 65500) # port is specific to peer
RFC_files = os.listdir(os.getcwd() + '/rfcs' + str(peerNumber)) # directory of peer's local RFC documents
RFC_index = [] # peer's RFC index list

# Create peer's RFC index
for fileName in RFC_files:
    RFC_index_entry = [] # one record in RFC index
    RFC_index_entry.append(int(''.join(filter(str.isdigit, fileName)))) # append RFC document number, index = 0
    # Get RFC title
    RFCfile = open('rfcs' + str(peerNumber) + '/' + fileName, 'rb')
    title = ''
    lineCount = 0
    for line in RFCfile.readlines():
        if lineCount == 3:
            title = title + line.lstrip().strip('\n') + ' '
        if((lineCount > 3) and (line == '\n')):
            break
        if((lineCount > 0) and (line == '\n')):
            lineCount += 1
        if b'ISSN' in line:
            lineCount = 1
    RFC_index_entry.append(title.rstrip()) # append RFC document title, index = 1
    RFC_index_entry.append(hostName) # append hostName of peer (localhost) that contains RFC documents, index = 2
    RFC_index_entry.append(TIMEOUT) # append TTL, index = 3
    RFC_index_entry.append(0) # download time, index = 4
    RFC_index_entry.append('') # local/remote, index = 5

    RFC_index.append(RFC_index_entry) # add this record to the peer's RFC index
    
def savePoint(numRFC, cumTime):
    dataFile = open('plot' + str(peerNumber) + '.txt', 'a')
    point = str(numRFC) + ',' + str(cumTime) + '\n'
    dataFile.write(point)
    dataFile.close()
#
def decrementTTL(): # decrement only for remote RFCs
    threading.Timer(10, decrementTTL).start() # gets called every 10 seconds
    RFC_index = server.getRFCindex()

    for entry in RFC_index:
        if(entry[5] == 'remote'): # remote RFCs
            entry[3] -= 10 # TTL
        else: # local RFCs
            entry[3] = TIMEOUT

def getRFCnumList():
    rfcidx = server.getRFCindex()
    rfcNumList = []
    for entry in rfcidx:
        rfcNumList.append(entry[0])
    return rfcNumList

# peer's RFC SERVER
server = RFCserver(hostName, portNumber, RFC_index, peerNumber)
RFCserverportnumber = server.getRFCserverportnumber()
threading.Thread(target=server.listen, args=()).start()

# peer's RFC CLIENT
client = RFCclient(RFCserverportnumber)
client.register() # peer registers with RS
sleep(15) # delay for peers to register with RS
activePeerList = client.pquery() # peer receives list of active peers from RS

#client.keepAlive() # periodically send KEEP ALIVE message to RS

#decrementTTL() # periodically decrement TTL values for remote peers in local peer's RFC index


# For each peer in active list, get its RFC index and its RFCs
numRFC = 0
totalTime = 0
RFC_num_list = getRFCnumList()
numDoc = len(RFC_num_list)
#cumStart = datetime.now()
for cookie, peer in activePeerList.items():
    if peer['portNumber'] != server.getRFCserverportnumber(): # don't care about checking for RFCs from itself
        try:			
            hostName = peer['hostname']
            neighborPort = peer['portNumber']
            # Receive RFC index from neighbor
            RFC_index_neighbor = client.rfcquery(hostName, neighborPort) # get RFC index of other peer
            RFC_index = server.getRFCindex() # get local peer's RFC index
            RFC_num_list = getRFCnumList()
            
            # NOTE: There can be multiple copies of RFCs
            # Get RFC
            for entry in RFC_index_neighbor: # would only want to download RFCs from neighbors
                if entry[0] not in RFC_num_list:
                    start = datetime.now() # start timing for downloading
                    client.getrfc(entry, hostName, neighborPort, peerNumber)
                    end = datetime.now() # end timing for downloading
                    diff = end - start
                    totalTime += diff.total_seconds()
                    entry[4] = diff.total_seconds() # download time
                    entry[5] = 'remote' # local/remote
                    numRFC += 1
                    savePoint(numRFC, totalTime)
                    #if numRFC == 50:
                    #    break
                    
            server.mergeRFCindex(RFC_index_neighbor) # merge local RFC index with other peer's RFC index
		            
        except:
            print('Peer: ' + str(hostName) + ' : ' + str(neighborPort) + ' is no longer active')
		    
print('\nTotal download time: ' + str(totalTime))
decrementTTL()

