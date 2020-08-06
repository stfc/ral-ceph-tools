#!/bin/bash

#Checks if the host can be connected to
host=$2
if ! timeout 10 ssh $host exit; then
    echo "Error: SSH connection failed"
    exit 1
fi
#Uses osdsearch to find the osd and parsed pathname
source ~/jamesf/osdsearch $1 $2
echo "Creating ticket..."
#Uses report_osd_alltypes to print a report of the osd
source ~/jamesf/report_osd_alltypes $osd > /tmp/osdreport
echo "" >> /tmp/osdreport
#Uses check_osd to verify if osd is ready to be removed
~/tom/check_osd.sh $2 $parsedpath >> /tmp/osdreport

#Creates the ticket in specific format
echo ""
echo "Status: new" > /tmp/driveticket
echo "Subject: Disk Replacement $1 on $2" >> /tmp/driveticket
echo "" >> /tmp/driveticket
echo -e "This drive has been ticketed for replacement using the ticket-drive script.\n" >> /tmp/driveticket
echo "$(cat /tmp/osdreport)" >> /tmp/driveticket
cat /tmp/driveticket

#Submits ticket via sendmail
read -p "Submit this ticket? (Y/N) " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    if ! timeout 10 sendmail ceph-disk@helpdesk.gridpp.rl.ac.uk < /tmp/driveticket
    then
        echo -e "\nTicket submission failed. (Ceph-Disk)"
        exit
    fi
    if ! timeout 10 sendmail hardware@helpdesk.gridpp.rl.ac.uk < /tmp/driveticket
    then
        echo -e "\nTicket submission failed. (Fabric-Hardware)"
        exit
    fi
    echo -e "\nTicket submitted to Ceph-Disk and Fabric-Hardware successfully!"
else
    echo -e "\nTicket was not submitted."
    exit 1
fi

#Uses linktickets to find the ticket IDs and link the two tickets together, then print a URL to them.
echo "Would you like to link the tickets together and receive a URL to them? (Y/N)"
read -p "Note: This will require RT credentials: " -n 1 -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
    subject="Disk Replacement $1 on $2"
    echo -e "\n"
    source ~/jamesf/linktickets $subject
    echo "Ceph-Disk ticket URL: https://helpdesk.gridpp.rl.ac.uk/Ticket/Display.html?id=${cephTicketID}"
    echo "Fabric-Hardware ticket URL: https://helpdesk.gridpp.rl.ac.uk/Ticket/Display.html?id=${fabricTicketID}"
else
    echo -e "\n"
    exit 1
fi
