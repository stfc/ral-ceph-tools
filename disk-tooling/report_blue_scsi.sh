#!/bin/bash
#Prints out parsed smartdata for bluestore SCSI drives.
host=$(ceph osd find $1 | jq -r '.crush_location.host')
dev=$(ceph osd metadata $1 | jq -r '.bluestore_bdev_partition_path' | cut -d '/' -f3)

echo $host

ssh $host smartctl -a -d scsi /dev/$dev > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

