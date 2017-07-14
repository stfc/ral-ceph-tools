#!/usr/bin/env python

'''
This programme locates the most recent dump file and then sorts all the first chunks into directories based upon their spacetokens. It removes the hex number from the end of the file names. It stores them in dump_date
'''

import gzip, os, re, time

def getFile(directory):
    files = os.listdir(directory)
    i = 0
    for a in files:
        date = re.match(r"(dumps_)([0-9]+)(.gz)", a)
        if date:
            if date.group(2) > i:
                i = date.group(2)
    newestDump = directory + "/dumps_" +  str(i) + ".gz"
    return newestDump


def sort(spacetoken, dump):
    date = time.strftime("%Y%m%d")
    fin = gzip.open(dump, "r")
    fout= open("/scratch/" + spacetoken + "/dumps/dump_" + date, "w")
    for line in fin:
        chunk0 = ".0000000000000000"
        if chunk0 not in line: 
            continue
        objectID = line.replace(chunk0, "")
        stlocation = objectID.split("/")[0]
        if spacetoken == stlocation:
           fout.write(objectID)

dump = getFile("/scratch")
sort("scratchdisk", dump)
sort("datadisk", dump)
