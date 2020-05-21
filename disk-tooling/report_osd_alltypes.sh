#!/bin/bash

if [[ $(($1)) != $1 ]]; then
   echo "Error: Input needs to be an OSD number"
   exit 1
fi

host=$(ceph osd find $1 | jq -r '.crush_location.host')
if [ -z "$host" ]; then
echo "Error: Could not find host location"
exit 1
fi
obj=$(ceph osd metadata $1 | jq -r '.osd_objectstore')
if [ -z "$obj" ]; then
echo "Error: Could not find OSD objectstore information"
exit 1
fi

#Identifies multipath host by running command conditionally
multipath_check() {
if ssh $1 multipath -ll ; then
  isMultipath=true
else
  isMultipath=false
fi
}
#Sends output to /dev/null to prevent it from displaying in console
multipath_check $host &> /dev/null

echo "Hostname is ${host}"

if [ "$obj" = 'filestore' ]; then
echo "OSD is filestore"

if [[ "$isMultipath" == true ]]; then
echo "Host is multipath"
else
echo "Host is not multipath"
fi

path=$(ceph osd metadata $1 | jq -r '.backend_filestore_partition_path' | cut -d '/' -f3)
disktype=$(ssh $host udevadm info --query=property /dev/$path | awk -F= -v key="ID_BUS" '$1==key {print $2}')

   if [ "$disktype" = 'scsi' ]; then

   ssh $host smartctl -a -d scsi /dev/$path > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

   elif [ "$disktype" = 'ata' ]; then

   ssh $host smartctl -a /dev/$path | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)';

   else
   echo "Error: unknown type of disk (Not ATA or SCSI)"
   exit 1
   fi

elif [ "$obj" = 'bluestore' ]; then
echo "OSD is bluestore"

vg=$(ssh $host ls -l /var/lib/ceph/osd/ceph-$1 | grep /dev | cut -d '/' -f3)

if [[ "$isMultipath" == true ]]; then
echo "Host is multipath"

part=$(ssh $host pvs --select vg_name=$vg | grep /dev/mapper | cut -d '/' -f4 | cut -d ' ' -f1)
type=$(ssh $host udevadm info --query=property /dev/mapper/$part | awk -F= -v key="ID_BUS" '$1==key {print $2}')

   if [ "$type" = 'ata' ]; then

   ssh $host smartctl -a /dev/mapper/$part | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)';

   else

   ssh $host smartctl -a -d scsi /dev/mapper/$part > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

   fi

elif [[ "$isMultipath" == false ]]; then
echo "Host is not multipath"

   part=$(ssh $host pvs --select vg_name=$vg | grep /dev | cut -d '/' -f3 | cut -d ' ' -f1)
   type=$(ssh $host udevadm info --query=property /dev/$part | awk -F= -v key="ID_BUS" '$1==key {print $2}')

   if [ "$type" = 'ata' ]; then

   ssh $host smartctl -a /dev/$part | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)';

   else

   ssh $host smartctl -a -d scsi /dev/$part > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

   fi
else
echo "Error: Could not detect if host is multipath or not"

fi
else
echo "Error: OSD is neither filestore nor bluestore"

fi
