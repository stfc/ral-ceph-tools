#!/bin/bash

#This script completely destroys all data on a disk, in an attempt to detect and fix any pending and uncorrectable sectors.
if [ $# -ne 1 ]; then
  echo "Usage should be: $0 [device eg. sdb]"
  exit 1
fi

exec &> /var/log/disk-recycling/${1}-full-check.txt

date

echo "Starting disk exercises on ${1}"

{
    smartctl -a /dev/${1} | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)'

    echo "Writing zeroes to disk"
    dd if=/dev/zero of=/dev/${1} 
    date
    smartctl -a /dev/${1} | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)'

    echo "Reading zeroes from disk"
    dd if=/dev/${1} of=/dev/null
    date
    smartctl -a /dev/${1} | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)'
} || {
    echo "error"
    exit 1
}

echo "Disk exercises complete."
date
