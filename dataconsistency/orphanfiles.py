#!/usr/bin/env python

'''
This programme searches a dump file to find any chunks without a first chunk. It then saves the names of these chunks to a seperate file to be deleted later. It sorts the file containing all the files in as it is quicker than running over the file multiple times
'''

import gzip, sys

input = sys.argv[1]
output = sys.argv[2]

fin = gzip.open(input, "r")
orphans = open(output, "w")
sortedfile = sorted(fin)
firstfile = sortedfile[0]
previousFile = firstfile[0:-18]
ffend = firstfile[-16:]
strippedffend = ffend.strip()
if strippedffend != "0000000000000000":
    lastOrphan = firstfile[0:-18]
else:
    lastOrphan = "a"

for line in sortedfile:
    strippedline = line.strip()
    end = strippedline[-16:]
    currentFile = line[0:-18]
    if currentFile == previousFile or end == "0000000000000000":
        if currentFile != lastOrphan:
            previousFile = currentFile
            continue
    orphans.write(line)
    previousFile = currentFile
    lastOrphan = currentFile
