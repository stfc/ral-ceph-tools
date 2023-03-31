hosts=`cat hostlist.txt`
# helper function to check if string is in list
function exists_in_list() {
    LIST=$1
    DELIMITER=$2
    VALUE=$3
    LIST_WHITESPACES=`echo $LIST | tr "$DELIMITER" " "`
    for x in $LIST_WHITESPACES; do
        if [ "$x" = "$VALUE" ]; then
            return 0
        fi
    done
    return 1
}

#run service operations on targetted services over multiple hosts
#example: bash serviceop.sh status xrootd@* reports the service status of all xrootd services on the hosts
#
if exists_in_list "start stop status restart" " " ${1}
then
  echo "start"
else
  echo "invalid op. valid ops are: start stop status restart"
  exit
fi
for t in ${hosts}; do
  echo "--------------------------------------------------------------------------------------------------------------"
  echo $t
  ( ssh root@${t} "systemctl ${1} ${2}" )
done
