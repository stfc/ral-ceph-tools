hosts=`cat hostlist.txt`
#run aq show_hosts over multiple hosts and searches for passed string
#example: basheckhost.sh Sandbox checks if hosts are in a sandbox
#
for t in ${hosts}; do
  echo "--------------------------------------------------------------------------------------------------------------"
  echo $t
  aq show_host --hostname ${t} | grep -i ${1}
done
