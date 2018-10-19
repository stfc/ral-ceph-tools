#!/bin/bash

#This script will go through every single drive in the devices list and wipe the data, excepting the boot drive.

echo "WARNING: This script will destroy all data on every non-boot drive."
read -p "Please confirm this is what you want to do by typing 'Confirm': "
if [ "$REPLY" != "Confirm" ]; then
    echo "Aborted"
    exit 1 
fi

for i in $(ls /dev | grep sd | grep -v 'sd[a-z]\{1,2\}[0-9]$'); do
    echo "cleaning $i"
    ./clean-disk.sh $i
done
wait
echo "Finished recycling"
