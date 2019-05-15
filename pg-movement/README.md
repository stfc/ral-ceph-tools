# Tools for analysing PG movement and OSD utilisation

## Notes:

* final-osd-util assumes that your PGs are either 3 replica, or EC 8+3, depending on PG set length, this is easy to change if your cluster differs
* I hadn't looked at the code in better-df for a while, but I clearly thought jq was really cool when I wrote it
* I would not advise useing these tool to guide your cluster operations without FIRST confirming they work as expected on your cluster, they were written in a hurry for a specific purpose and may not work as expected elsewhere.

## Example:

~~~~
[root@ceph-adm1 ~]# better-df | head
ID        crush  rewgt   size      free    util      PGs   on   off
osd.20    5.458  1.000   5577GB   836GB    85.0%     58    0↑    1↓
osd.119   5.458  1.000   5577GB   842GB    84.9%     59    3↑    0↓
osd.94    5.458  1.000   5577GB   847GB    84.8%     40    0↑    1↓
osd.76    5.458  1.000   5577GB   864GB    84.5%     59    0↑    0↓
[root@ceph-adm1 ~]# final-osd-util 119
93.2
[root@ceph-adm1 ~]# ceph osd reweight 119 0.95
reweighted osd.119 to 0.95
[root@ceph-adm1 ~]# final-osd-util 119
87.2
~~~~
