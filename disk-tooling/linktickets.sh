#!/bin/bash
serial=$1
#RT credentials
read -p "Enter RT Username: " USERNAME
read -s -p "Enter RT Password: " PASSWORD ; echo ""
#Uses RT credentials to get a list of tickets in Ceph-Disk and Fabric-Hardware queues, obtaining the ticket ID and the subject.
#Saves these queues to a tmp file, sorted by newest ticket at the top.
if ! wget --keep-session-cookies --save-cookies /tmp/cookies.txt --post-data="user=$USERNAME&pass=$PASSWORD" --no-check-certificate -O /tmp/cephdiskqueue  https://helpdesk.gridpp.rl.ac.uk/REST/1.0/search/ticket?query="Queue='Ceph-Disk'&orderby=-Created" &> /dev/null ; then
    echo "Failed to connect to RT"
    exit 1
fi
if ! wget --keep-session-cookies --save-cookies /tmp/cookies.txt --post-data="user=$USERNAME&pass=$PASSWORD" --no-check-certificate -O /tmp/hardwarequeue  https://helpdesk.gridpp.rl.ac.uk/REST/1.0/search/ticket?query="Queue='Fabric-Hardware'&orderby=-Created" &> /dev/null ; then
    echo "Failed to connect to RT"
    exit 1
fi
#Exits if credentials were incorrect.
if grep -q "Credentials required" /tmp/cephdiskqueue; then
    echo "RT Username or Password are incorrect."
    exit 1
fi
if grep -q "Credentials required" /tmp/hardwarequeue; then
    echo "RT Username or Password are incorrect."
    exit 1
fi
#The ticket list is then searched by subject to find the appropriate ticket. When a match is found, the search ends.
#If a match isn't found, it ends the script.
#The ID of the ticket is then parsed from the list.
cephTicketID="$(grep "$serial" /tmp/cephdiskqueue | awk -F: '{print $1}' | head -1)"
if [ -z "$cephTicketID" ]; then
    echo "Ceph-Disk Ticket ID not found."
    exit 1
fi
fabricTicketID="$(grep "$serial" /tmp/hardwarequeue | awk -F: '{print $1}' | head -1)"
if [ -z "$fabricTicketID" ]; then
    echo "Fabric-Hardware Ticket ID not found."
    exit 1
fi

echo "Ceph-Disk Ticket ID: ${cephTicketID}"
echo "Fabric-Hardware Ticket ID: ${fabricTicketID}"

#Makes the Ceph-Disk ticket depend on the Fabric-Hardware ticket by posting the ticketlink file.
echo "DependsOn: $fabricTicketID" > /tmp/ticketlink
if ! curl -k --data-urlencode content@/tmp/ticketlink "https://helpdesk.gridpp.rl.ac.uk/REST/1.0/ticket/$cephTicketID/links?user=$USERNAME&pass=$PASSWORD" ; then
    echo "Failed to curl ticketlink file to RT"
    exit 1
fi

#Unsets the password variable for security.
unset PASSWORD
