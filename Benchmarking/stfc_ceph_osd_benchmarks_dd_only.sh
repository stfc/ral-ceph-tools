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

osds=$(mount | grep xfs | cut -f 3 -d ' ' | grep -xv /)

if [ -z "$osds" ]; then
    echo "ERROR: Couldn't find any mounted OSD disks"
    exit 1
fi

echo "Running benchmarks, this will take some time, be patient!"

date -I > /tmp/results


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


cat /tmp/results
