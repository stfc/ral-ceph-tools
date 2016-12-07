#!/bin/bash

function cleanup {
    # Remove stray test files
    echo -e "\n---- Cleanup ----"
    for osd in $osds; do
        echo -n .
        rm -f $osd/testfile &
    done
    wait
    sync
}

osds=$(awk '/osd/ { print $2 }' /etc/mtab)

if [ -z "$osds" ]; then
    echo "ERROR: Couldn't find any mounted OSD disks"
    exit 1
fi

echo "Running benchmarks, this will take some time, be patient!"

date -I > /tmp/results
ceph version >>/tmp/results


# dd based tests of each filesytem

echo -e "\n---- Single Write ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    echo -e "$osd\t$(dd if=/dev/zero of=$osd/testfile bs=1G count=1 oflag=direct 2>&1 | awk '/copied/ { print $8 }')" >> /tmp/results
done
cleanup

echo -e "\n---- Parallel Write ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    echo -e "$osd\t$(dd if=/dev/zero of=$osd/testfile bs=1G count=1 oflag=direct 2>&1 | awk '/copied/ { print $8 }')" >> /tmp/results &
done
wait

echo -e "\n---- Single Read ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    echo -e "$osd\t$(dd if=$osd/testfile of=/dev/null bs=1G count=1 iflag=direct 2>&1 | awk '/copied/ { print $8 }')" >> /tmp/results
done

echo -e "\n---- Parallel Read ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    echo -e "$osd\t$(dd if=$osd/testfile of=/dev/null bs=1G count=1 iflag=direct 2>&1 | awk '/copied/ { print $8 }')" >> /tmp/results &
done
wait
cleanup


# Ceph based tests of each OSD

echo -e "\n---- Single OSD Bench ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    id=$(cat $osd/whoami)
    echo -e "$osd\t$(ceph tell osd.$id bench 2>&1 | awk '/bytes_per_sec/ { print $NF }')" >> /tmp/results
done

echo -e "\n---- Parallel OSD Bench ----" | tee -a /tmp/results
for osd in $osds; do
    echo -n .
    id=$(cat $osd/whoami)
    echo -e "$osd\t$(ceph tell osd.$id bench 2>&1 | awk '/bytes_per_sec/ { print $NF }')" >> /tmp/results &
done
wait

echo -e "\n----" | tee -a /tmp/results
echo "Complete"
echo

cat /tmp/results
