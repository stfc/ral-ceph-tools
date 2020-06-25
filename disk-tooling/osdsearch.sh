#!/bin/bash

host=$2
multipath_check() {
if timeout 10 ssh $1 multipath -ll ; then
    isMultipath=true
else
    isMultipath=false
fi
}

multipath_check $host &> /dev/null

path=""
parsedpath=""

if [[ "$isMultipath" == true ]]; then

    for i in $(ssh $host "ls /dev/mapper/*" | grep -v [0-9] | grep -v control ); do if ( ssh $host smartctl -a -d scsi $i | grep $1 ); then path="$i"; break; fi; done

    vg=$(ssh $host pvs | grep $path | awk '{print $2}' )
    osd=$(ssh $host ls -l /var/lib/ceph/osd/ceph-*/block 2>/dev/null | grep "$vg" 2>/dev/null | cut -d'/' -f6 | cut -d'-' -f2)
    parsedpath=$(ssh $host echo "$path" | cut -d '/' -f4)

else
    for i in $(ssh $host "ls /dev/sd*" | grep -v [0-9] ); do if ( ssh $host smartctl -a $i | grep $1 ); then path="$i"; break; fi; done

    osd=$(ssh $host df | grep "${path}1"| cut -d'-' -f2)
    parsedpath=$(ssh $host echo "${path%1}" | cut -d '/' -f3)
fi

echo "$parsedpath"
echo "$osd"
