#!/usr/bin/bash

# Usage: compact.sh <OSD ID>
# Will identify the host the OSD lives on
# Log on, set the compact on mount option
# Restart the OSD, wait for HEALTH_OK
# Remove the option and restart the OSD again
# Wait for HEALTH_OK again then measure the
# size of the LevelDB and report it
# Requires:
#  * ceph
#  * jq
#  * ceph.conf
#  * keyring with 'allow mon r'
#  * SSH private key logins

osd=$1
host=$(ceph osd find $osd | jq -r '.crush_location.host').gridpp.rl.ac.uk
cmd_omapsz="du -sh /var/lib/ceph/osd/ceph-$osd/current/omap/"
cmd_set_compact="sed -i.bak '$ a\
leveldb_compact_on_mount = true' /etc/ceph/ceph.conf
"
cmd_unset_compact="sed -i '/leveldb_compact_on_mount/d' /etc/ceph/ceph.conf
"
cmd_restart="systemctl restart ceph-osd@$osd"

ceph_health=$(ceph health)

echo "Compacting LevelDB for osd.$osd on $host"

if [ "$ceph_health" == 'HEALTH_OK' ]
    then
    echo "Health is OK... proceeding"
    ssh -A -o StrictHostKeyChecking=no root@$host "$cmd_set_compact"
    ssh -A -o StrictHostKeyChecking=no root@$host "$cmd_restart"
else
    echo "Could not restart and comapct osd.$osd, health NOT OK"
fi

echo -n "Checking health is OK before proceeding..."
ceph_health=$(ceph health)
while [ "$ceph_health" != 'HEALTH_OK' ]; do
    sleep 30
    ceph_health=$(ceph health)
done

echo "HEALTH OK"
echo "Unsetting leveldb_compact_on_mount and restarting osd.$osd"
ssh -A -o StrictHostKeyChecking=no root@$host "$cmd_unset_compact"
ssh -A -o StrictHostKeyChecking=no root@$host "$cmd_restart"
echo -n "Waiting for healthy cluster..."
ceph_health=$(ceph health)
while [ "$ceph_health" != 'HEALTH_OK' ]; do
    sleep 30
    ceph_health=$(ceph health)
done
echo "OK. Checking new size:"

ssh -A -o StrictHostKeyChecking=no root@$host "$cmd_omapsz"
