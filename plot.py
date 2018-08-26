#!/usr/bin/env python

"""
ECE 573 Project 1
Venkata Surya Teja Penumatcha
Michael Patel

This is Plot
"""

import matplotlib.pyplot as plt


cumTime = []
numRFC = []

"""
# Place this code in peer to save the data point
# Write to file
dataFile = open('plot.txt', 'wb')
point = str(200) + ',' + str(12) + '\n'
dataFile.write(point)
point = str(400) + ',' + str(16) + '\n'
dataFile.write(point)
dataFile.close()
"""

# Read values
for i in range(1, 7): # peers 1-6
	try:
		timeRecord = []
		rfcRecord = []
		dataFile = open('plot' + str(i) + '.txt', 'r')
		for line in dataFile.readlines():
			timeRecord.append(float(line.split(',', 1)[1]))
			rfcRecord.append(float(line.split(',', 1)[0]))
		cumTime.append(timeRecord)
		numRFC.append(rfcRecord)
	except:
		#break
		print(i)
# Setting y-axis range
maxCumTime = max(max(cumTime))
maxNumRFC = max(max(numRFC))
#if(len(cumTime) > 0):
plt.ylim(0, 5)
if(len(numRFC) > 0):
    plt.xlim(0, maxNumRFC*1.25)

color = ['r-', 'g-', 'b-', 'k-', 'm-', 'c-']
labels = ['Peer1', 'Peer2', 'Peer3', 'Peer4', 'Peer5', 'Peer6']

for i in range(1, 7):
	try:
		plt.plot(numRFC[i-1], cumTime[i-1], color[i-1], label=labels[i-1])
	except:
		print(i)
		#break

plt.xlabel('Number of RFCs')
plt.ylabel('Cumulative download time (s)')
plt.title('File Distribution')
plt.legend(loc = 'best')
plt.savefig("plot.png")
