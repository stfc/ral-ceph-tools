hosts=`cat hostlist.txt`
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
