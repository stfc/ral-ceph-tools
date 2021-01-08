#!/usr/bin/python3
import os
import re
import sys
import json
import argparse
from datetime import datetime, timedelta

def readable_timedelta(duration: timedelta):
    data = {}
    data['d'], remaining = divmod(duration.total_seconds(), 86_400)
    data['h'], remaining = divmod(remaining, 3_600)
    data['m'], data['s'] = divmod(remaining, 60)

    time_parts = [f'{round(value)}{name}' for name, value in data.items() if value > 0]
    if time_parts:
        return ' '.join(time_parts)
    else:
        return '<1s'


pattern = re.compile("^{.*}$")

OK = 0
WARN = 1
CRIT = 2
UNKNOWN = 3

check_time = datetime.now()

parser = argparse.ArgumentParser(description="Check the status of a backup run by the CephFS recursive-backup script.")

parser.add_argument("log", help="log file from backup process")
parser.add_argument("interval", help="time allowed since last successful backup (in seconds)", type=int)

args = parser.parse_args()

try:
    interval_delta = timedelta(seconds=args.interval)
    allowed_last_time = check_time - interval_delta
except:
    print("Error parsing last allowed backup time")
    sys.exit(CRIT)

if not os.path.isfile(args.log):
    print ("Backup log file does not exist")
    sys.exit(CRIT)

last_summary="NONE"
try:
    for i, line in enumerate(open(args.log)):
        for match in re.finditer(pattern, line):
            last_summary = match.group()
            #print("Found on line {}: {}".format(i+1, match.group()))
except:
    print("Error reading backup log file")
    sys.exit(CRIT)

if last_summary is "NONE":
    print("No backup summary found in log file")
    sys.exit(CRIT)

try:
    summary = json.loads(last_summary)
except: 
    print("Error parsing JSON summary")
    sys.exit(CRIT)

if "type" not in summary:
    print("Error reading JSON summary: message type not in object")
    sys.exit(CRIT)

if summary["type"] != "backup_summary":
    print("Error reading JSON summary: message type is not backup_summary")
    sys.exit(CRIT)

if "message" not in summary:
    print("Error reading JSON summary: summary message not in object")
    sys.exit(CRIT)

if "success" not in summary:
    print("Error reading JSON summary: summary success status not in object")
    sys.exit(CRIT)

if summary["success"] != True:
    print("Last backup was not successful: {}".format(summary["message"]))
    sys.exit(CRIT)

if "start_time" not in summary:
    print("Error reading JSON summary: start time not in object")
    sys.exit(CRIT)

try:
    start_time = datetime.fromtimestamp(summary["start_time"])
except:
    print("Error reading JSON summary: start time not parsable")
    sys.exit(CRIT)

if "exit_time" not in summary:
    print("Error reading JSON summary: exit time not in object")
    sys.exit(CRIT)

try:
    exit_time = datetime.fromtimestamp(summary["exit_time"])
except:
    print("Error reading JSON summary: exit time not parsable")
    sys.exit(CRIT)

#if start_time.timestamp() < allowed_last_time.timestamp():
if start_time < allowed_last_time:
    print( "Last successful backup started at {}, longer ago than the backup interval of {}".format(readable_timedelta(check_time - start_time), readable_timedelta(interval_delta)) )
    sys.exit(CRIT)

print("A successful backup started {} ago and ran for {}. The backup interval is {}". format(readable_timedelta(check_time - start_time), readable_timedelta(exit_time - start_time), readable_timedelta(interval_delta)))
sys.exit(OK)
