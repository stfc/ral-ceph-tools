#!/bin/bash

#Input sanitization, uses a regular expression which will fail if input contains non-integer characters
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: Input needs to be a valid OSD number"
    exit 1
fi

#Locates the host
host=$(timeout 10 ceph osd find $1 | jq -r '.crush_location.host')
if [ -z "$host" ]; then
    echo "Error: Could not find host location"
    exit 1
fi
#Finds objectstore type
obj=$(timeout 10 ceph osd metadata $1 | jq -r '.osd_objectstore')
if [ -z "$obj" ]; then
    echo "Error: Could not find OSD objectstore information"
    exit 1
fi
#Checks if SSH successfully connects, exits script if it doesn't
if ! timeout 10 ssh $host exit; then
    echo "Error: SSH connection failed"
    exit 1
fi
#Identifies the hardware generation of host
gen=$(timeout 10 ssh $host /usr/sbin/ccm --format json /hardware | jq -r '.model')
if [ -z "$gen" ]; then
    echo "Error: Could not identify hardware generation"
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

echo "Hostname: ${host}"
echo "Hardware Generation: ${gen}"

if [ "$obj" = 'filestore' ]; then
    echo "OSD: Filestore"

    if [[ "$isMultipath" == true ]]; then
        echo "Multipath: Yes "
    else
        echo "Multipath: No"
    fi
    #Locates the partition path i.e. sda, then uses udev info to identify if the disk type is SATA or SAS
    path=$(timeout 10 ceph osd metadata $1 | jq -r '.backend_filestore_partition_path' | cut -d '/' -f3)
    echo "Path: /dev/$path"
    disktype=$(timeout 10 ssh $host udevadm info --query=property /dev/$path | awk -F= -v key="ID_BUS" '$1==key {print $2}')

    if [ "$disktype" = 'scsi' ]; then
        #Filestore SAS
        if ! timeout 10 ssh $host smartctl -a -d scsi /dev/$path > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}'; then
            echo "Error: smartctl failed to find path"
            exit 1
        fi

    elif [ "$disktype" = 'ata' ]; then
        #Filestore SATA
        if ! timeout 10 ssh $host smartctl -a /dev/$path | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)'; then
            echo "Error smartctl failed to find path"
            exit 1
        fi

    else
        #Exception check
        echo "Error: unknown type of disk (Not ATA or SCSI)"
        exit 1
    fi

elif [ "$obj" = 'bluestore' ]; then
    echo "OSD: Bluestore"

    vg=$(timeout 10 ssh $host ls -l /var/lib/ceph/osd/ceph-$1 | grep /dev | cut -d '/' -f3)

    if [[ "$isMultipath" == true ]]; then
        echo "Multipath: Yes"
        #Uses the volume group to find the /dev/mapper partition path, then udev to identify SATA or SAS
        part=$(timeout 10 ssh $host pvs --select vg_name=$vg | grep /dev/mapper | cut -d '/' -f4 | cut -d ' ' -f1)
        echo "Path: /dev/mapper/$part"
        disktype=$(timeout 10 ssh $host udevadm info --query=property /dev/mapper/$part | awk -F= -v key="ID_BUS" '$1==key {print $2}')

        if [ "$disktype" = 'ata' ]; then
            #Bluestore multipath SATA
            timeout 10 ssh $host smartctl -a /dev/mapper/$part | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)';
            if $? > 0; then
                echo "Error: smartctl failed to find mpath"
                exit 1
            fi

        else
            #Bluestore multipath SAS
            timeout 10 ssh $host smartctl -a -d scsi /dev/mapper/$part > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

        fi

    else
        echo "Multipath: No"
        #Non-multipath uses the same method to identify SATA/SAS, but the parsing is different
        part=$(timeout 10 ssh $host pvs --select vg_name=$vg | grep /dev | cut -d '/' -f3 | cut -d ' ' -f1)
        echo "Path: /dev/$part"
        disktype=$(timeout 10 ssh $host udevadm info --query=property /dev/$part | awk -F= -v key="ID_BUS" '$1==key {print $2}')

        if [ "$disktype" = 'ata' ]; then
            #Bluestore non-multipath SATA
            if ! timeout 10 ssh $host smartctl -a /dev/$part | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)'; then
                echo "Error: smartctl failed to find path"
                exit 1
            fi

        else
            #Bluestore non-multipath SAS
            if ! timeout 10 ssh $host smartctl -a -d scsi /dev/$part > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}'; then
                echo "Error: smartctl failed to find path"
                exit 1
            fi

        fi
    fi
else
    #Exception check
    echo "Error: OSD is neither filestore nor bluestore"
    exit 1
fi
