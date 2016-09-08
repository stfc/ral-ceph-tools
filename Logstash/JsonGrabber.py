import json, re, types, sys, subprocess, os, time
from subprocess import call
import datetime
now = datetime.datetime.now()
if len(str(now.day)) == 1:
    nowday = "0"+str(now.day)
else:
    nowday = str(now.day)
if len(str(now.month)) == 1:
    nowmonth = "0"+str(now.month)
else:
    nowmonth = str(now.month)
datevar = str(now.year)+nowmonth+"-"+nowday+"-"+str(now.hour)
Path = "/tmp/Russell/" #path for files
os.system("radosgw-admin"+" log list > "+Path+"loglist.txt") #runs the command to grab loglist
with open(Path+'loglist.txt') as f:
    list1 = f.readlines()
    for key in list1:
        a = key.strip()
        b = a.strip('"')
        c = b.rstrip('",') #line 9,10 & 11 all strip certain characters from the logs
        if c.startswith(datevar):
            try:
                output = c+".json"
                os.system("radosgw-admin"+" log"+" show "+"--object="+c+" > "+Path+output) #runs command to grab the log file
                myfile = open(Path+"NW"+output,"w")
                with open(Path+output, "r") as FILE:
                    FILED = json.load(FILE)
                    FILED = FILED["log_entries"]
                    for i, item in enumerate(FILED):
                        myfile.write(json.dumps(item)) #writes the item to a line
                        myfile.write("\n") #adds newline so the entire file isnot a single line
                    myfile.close()
            except:
                print "loglist is empty"
os.remove(Path+"loglist.txt")
os.remove(Path+output) #removes original log file
