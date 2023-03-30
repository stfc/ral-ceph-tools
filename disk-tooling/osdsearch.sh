#!/bin/bash

#Checks if host can be connected to
host=$2
if ! timeout 10 ssh $host exit; then
    echo "Error: SSH connection failed"
    exit 1
fi
#Multipath identification
#Compares the output of pvs on the host to see if it contains mapper.
#If it does, the host is multipath. If not, it is not.
if ! ssh $host pvs &> /dev/null ; then
    echo "Error: Could not run pvs for multipath check"
    exit 1
fi
multicheck=$(timeout 10 ssh $host pvs 2>/dev/null)
if echo "$multicheck" | grep -q "mapper" ; then
    isMultipath=true
else
    isMultipath=false
fi

path=""
parsedpath=""

echo "Searching for OSD..."
if [[ "$isMultipath" == true ]]; then
#If the host is multipath, search for /dev/mapper
    for i in $(timeout 10 ssh $host "ls /dev/mapper/*" | grep -v [0-9] | grep -v control ); do if (timeout 10 ssh $host smartctl -a -d scsi $i | grep $1 ); then path="$i"; break; fi; done
#Use the path to find the VG
    vg=$(timeout 10 ssh $host pvs | grep $path | awk '{print $2}' )
    if [ -z "$vg" ]; then
        echo "Error: Volume Group not found"
        exit 1
    fi
#Use the VG to search for the OSD number
    osd=$(timeout 10 ssh $host ls -l /var/lib/ceph/osd/ceph-*/block 2>/dev/null | grep "$vg" 2>/dev/null | cut -d'/' -f6 | cut -d'-' -f2)
#OSD sanitization
    if [ -z "$osd" ]; then
        echo "Error: OSD not found"
        exit 1
    fi
    if ! [[ "$osd" =~ ^[0-9]+$ ]]; then
        echo "Error: OSD not found"
        exit 1
    fi
#Parsing the pathname to only have the last part, i.e mpatha
    parsedpath=$(timeout 10 ssh $host echo "$path" | cut -d '/' -f4)
    if [ -z "$parsedpath" ]; then
        echo "Error: Could not parse path correctly"
        exit 1
    fi

else
#If the host is not multipath, search for /dev/sd
#The pathname can then be used to search directly for the OSD
    for i in $(timeout 10 ssh $host "ls /dev/sd*" | grep -v [0-9] ); do if (timeout 10 ssh $host smartctl -a $i | grep $1 ); then path="$i"; break; fi; done
    osd=$(timeout 10 ssh $host df | grep "${path}1"| cut -d'-' -f2)
#If this fails, the OSD is a bluestore
    if [ -z "$osd" ]; then
#Search for the VG using the pathname instead, then use the VG to find the OSD
        vg=$(timeout 10 ssh $host pvs | grep $path | awk '{print $2}' )
        if [ -z "$vg" ]; then
            echo "Error: Volume Group not found"
            exit 1
        fi
        osd=$(timeout 10 ssh $host ls -l /var/lib/ceph/osd/ceph-*/block 2>/dev/null | grep "$vg" 2>/dev/null | cut -d'/' -f6 | cut -d'-' -f2)
        if [ -z "$osd" ]; then
            echo "Error: OSD not found"
            exit 1
        fi
    fi
    if ! [[ "$osd" =~ ^[0-9]+$ ]]; then
        echo "Error: OSD not found"
        exit 1
    fi
#Parsing the pathname to only have the last part, i.e sdaa
    parsedpath=$(timeout 10 ssh $host echo "${path%1}" | cut -d '/' -f3)
    if [ -z "$parsedpath" ]; then
        echo "Error: Path parsing failed (OSD not found)"
        exit 1
    fi
fi

echo "${parsedpath} is the path"
echo "${osd} is the OSD number"
