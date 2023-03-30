#!/bin/bash
#Saves smartdata to a temporary file, then uses multiple searches to parse it.

smartctl -a /dev/$1 > /tmp/smartdata_temp

cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}'
