#!/bin/bash

if [[ $(($1)) != $1 ]]; then
   echo "Error: Input needs to be an OSD number"
   exit 1
fi

host=$(ceph osd find $1 | jq -r '.crush_location.host')
obj=$(ceph osd metadata $1 | jq -r '.osd_objectstore')

multipath_check() {
if ssh $1 multipath -ll ; then
  isMultipath=true
else
  isMultipath=false
fi
}

multipath_check $host &> /dev/null

echo "Hostname is ${host}"

if [ "$obj" = 'filestore' ]; then
echo "OSD is filestore"

dev=$(ceph osd metadata $1 | jq -r '.backend_filestore_partition_path' | cut -d '/' -f3)
type=$(ssh $host udevadm info --query=property /dev/$dev | awk -F= -v key="ID_BUS" '$1==key {print $2}')

   if [ "$type" = 'scsi' ]; then

   ssh $host smartctl -a -d scsi /dev/$dev > /tmp/smartdata_temp; cat /tmp/smartdata_temp | grep -E 'Serial|Vendor:|Product:|Status:' && cat /tmp/smartdata_temp | grep -B1 -A1 uncorrected | awk '{print $NF}' | paste -sd ' ' && cat /tmp/smartdata_temp | grep -A2 read: | awk '{print $1 $NF}';

   elif [ "$type" = 'ata' ]; then

   ssh $host smartctl -a /dev/$dev | grep -E '(Serial|Model|Raw_Read_Error_Rate|Current_Pending_Sector|Offline_Uncorrectable)';

   else
   echo "Error: unknown type of disk (Not ATA or SCSI)"

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
