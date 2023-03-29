hosts=( "ceph-gw4.gridpp.rl.ac.uk" "ceph-gw5.gridpp.rl.ac.uk" "ceph-gw6.gridpp.rl.ac.uk" "ceph-gw7.gridpp.rl.ac.uk" "ceph-gw10.gridpp.rl.ac.uk" "ceph-gw11.gridpp.rl.ac.uk" "ceph-gw15.gridpp.rl.ac.uk" "ceph-gw16.gridpp.rl.ac.uk" "ceph-svc01.gridpp.rl.ac.uk" "ceph-svc02.gridpp.rl.ac.uk" "ceph-svc03.gridpp.rl.ac.uk" "ceph-svc05.gridpp.rl.ac.uk" "ceph-svc97.gridpp.rl.ac.uk" "ceph-svc98.gridpp.rl.ac.uk" "ceph-svc99.gridpp.rl.ac.uk" );
#searches xrootd and gridftp logs and ip address gw hosts listed above for parameter passed to script
#example: bash logsearch.sh 31.147.202.178 searches for that ip address in logs and ssh
#
for t in ${hosts[@]}; do
  echo "--------------------------------------------------------------------------------------------------------------"
  echo $t
  ( ssh root@${t} "cat /var/log/xrootd/unified/xrootd.log | grep -i \"${1}\"")
  ( ssh root@${t} "cat /var/log/gridftp/* | grep -i \"${1}\"")
  ( ssh root@${t} "ss -a | grep -i \"${1}\"")
done
