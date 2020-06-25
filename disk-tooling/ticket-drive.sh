#!/bin/bash

host=$2
echo "Creating ticket..."
source ~/jamesf/osdsearch $1 $2 &> /dev/null
source ~/jamesf/report_osd_alltypes $osd > /tmp/osdreport
echo "" >> /tmp/osdreport
~/tom/check_osd.sh $2 $parsedpath >> /tmp/osdreport

echo "Status: new" > /tmp/driveticket
echo "Subject: Disk Replacement $1 on $2" >> /tmp/driveticket
echo "" >> /tmp/driveticket
echo -e "This drive has been ticketed for replacement using the ticket-drive script.\n" >> /tmp/driveticket
echo "Path: $parsedpath" >> /tmp/driveticket
echo "$(cat /tmp/osdreport)" >> /tmp/driveticket
cat /tmp/driveticket

read -p "Submit this ticket? (Y/N) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    if ! sendmail ceph-disk@helpdesk.gridpp.rl.ac.uk < /tmp/driveticket
    then
        echo -e "\nTicket submission failed. (Ceph-Disk)"
    fi
    if ! sendmail hardware@helpdesk.gridpp.rl.ac.uk < /tmp/driveticket
    then
        echo -e "\nTicket submission failed. (Fabric-Hardware)"
    fi
    echo -e "\nTicket submitted to Ceph-Disk and Fabric-Hardware successfully!"
else
    echo -e "\nTicket was not submitted."
    exit 1
fi
