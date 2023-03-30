#!/bin/bash
#test comment for git
#This script will unmount and wipe the partitions from a drive.

if [ $# -ne 1 ]; then
  echo "Usage should be: $0 [device] eg. sdb"
  exit 1
fi

date

df | grep -q  "${1}[0-9]"

if [ $? -eq 0 ] ; then
    if [ $(df | grep "${1}[0-9]" | grep -q '[[:space:]]\/$'; echo $?) -eq 0 ]; then
        echo "This is the boot drive"
        exit 2
    fi
    for i in $(df | grep "${1}[0-9]" | cut -d ' ' -f 1); do
        umount ${i}
    done
fi

wipefs -a -f /dev/${1}

/usr/bin/exorcise-disk.sh ${1}
