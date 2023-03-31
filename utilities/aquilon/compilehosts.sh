hosts=`cat hostlist.txt`
#compiles all hosts in the hostlist file
#example: bash compilehosts.sh 
#
for t in ${hosts}; do
  echo "--------------------------------------------------------------------------------------------------------------"
  echo $t
  aq compile --hostname ${t} 
done
