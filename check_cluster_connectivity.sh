#!/bin/bash
# give script a list of hosts and it will ssh to them, find their cluster IPs and they attempt to establish if the cluster connectivity is good
#set -e

TOTAL_PAD=2

FLUSH_ARP=${FLUSH_ARP:-0}

RATE_LIMIT=0.05 # seconds to wait between parallel calls

RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
GREY=$(tput setaf 8)
NC=$(tput sgr0)

hn_len=1

hostname_arr=()
publicip_arr=()
clusterip_arr=()

results_dir="$(mktemp -d /tmp/check_cluster_connectivity.XXXXXXXXXX)"

find_ips () {
    nice ssh -o "StrictHostKeyChecking=no" "$1" ip -o a 2>/dev/null | grep -o "1\(0\|30\).246.[0-9]\+.[0-9]\+/[0-9]\+" | cut -d / -f 1 | sort -r | xargs echo > "$results_dir/$1/ips"
    echo -n '·'
}

flush_arp () {
    echo "flushing arp cache on $1"
    nice ssh -o "StrictHostKeyChecking=no" "$1" ip neigh flush all
    echo -n '·'
}

check_ping () {
    host="$1"
    shift
    network="$1"
    shift
    nice ssh -o "StrictHostKeyChecking=no" "$host" "fping $@" 2>/dev/null | grep -vF ' error ' 1>>"$results_dir/$host/$network"
    echo $? > "$results_dir/$host/exit"
    echo -n '.'
}

pass_fail () {
    host="$1"
    network="$2"
    dest="$3"
    if [[ $(cat "$results_dir/$host/exit") -le 1 ]]; then
        state="$(awk "/^$dest is/ {print \$NF}" "$results_dir/$host/$network")"
        if [[ "$state" == "alive" ]]; then
            echo -ne "✓ "
        elif [[ "$state" == "unreachable" ]]; then
            echo -ne "✗ "
        else
            echo "?"
        fi
    else
        echo -ne "!"
    fi
}

pad_print () {
    if [[ "$1" == "✓ " ]]; then
        printf "${GREEN}%-${TOTAL_PAD}s${NC}" "$1"
    elif [[ "$1" == "✗ " ]]; then
        printf "${RED}%-${TOTAL_PAD}s${NC}" "$1"
    elif [[ "$1" == "!" || "$1" == "?" ]]; then
        printf "${YELLOW}%-${TOTAL_PAD}s${NC}" "$1"
    elif [[ "$1" == '· ' ]]; then
        printf "${GREY}%-${TOTAL_PAD}s${NC}" "$1"
    else
        printf "%-${TOTAL_PAD}s" "$1"
    fi
}

print_header () {
    echo
    for _ in $(seq 1 "$(tput cols)"); do
        echo -n "─"
    done
    echo -e "\r──┤ $1 ├"
}

# Sort list of hostnames using version sort
hosts="$(echo "$@" | xargs -n 1 echo | sort -V | uniq)"


print_header "Gathering IP addresses"
for host in $hosts; do
    mkdir -p "$results_dir/$host"
    find_ips "$host" &
    sleep $RATE_LIMIT
done
wait
echo


if [[ $FLUSH_ARP -eq 1 ]]; then
    print_header "Flushing ARP caches"
    for host in $hosts; do
    mkdir -p "$results_dir/$host"
    flush_arp "$host" &
    sleep $RATE_LIMIT
    done
    wait
    echo
fi


print_header "Checking Consistency"
for host in $hosts; do
    read -r publicip clusterip < "$results_dir/$host/ips"
    if [[ -z "$publicip" ]]; then
        pad_print "✗ "
        printf "%-12s %s\n" "$host" "no public ip found, exiting"
        exit 1
    fi

    if [[ -z "$clusterip" ]]; then
        pad_print "✗ "
        printf "%-12s %s\n" "$host" "no cluster ip found, exiting"
        exit 1
    else
        pad_print "✓ "
        printf "%-12s %-15s %-15s\n" "$host" "$publicip" "$clusterip"
        hostname_arr+=( "$host" )
        publicip_arr+=( "$publicip" )
        clusterip_arr+=( "$clusterip" )
    fi
    # find length of hostnames for matrix formatting purposes
    hostname_len=$(( ${#host} + 1))
    if [[ $hostname_len -gt $hn_len ]]; then
        hn_len=$hostname_len
    fi
done

echo
pad_print "✓ "
echo "IPs found for all hosts"


# sanity check our arrays against input args and each other
if [[ ${#hostname_arr[@]} -ne $# ]] || [[ ${#hostname_arr[@]} -ne ${#publicip_arr[@]} ]] || [[ ${#clusterip_arr[@]} -ne ${#publicip_arr[@]} ]]
then
    declare -p hostname_arr
    declare -p publicip_arr
    declare -p clusterip_arr
    echo "wrong number of hosts, public or private addresses found, something went wrong, exiting"
    exit 1
fi


print_header "Running Ping Tests"
printf "Estimated time: %.0f seconds\n" "$(echo "${#hostname_arr[@]} * $RATE_LIMIT * 2" | bc -l)"
for i in "${!hostname_arr[@]}"; do
    host="${hostname_arr[i]}"
    dest="${publicip_arr[@]}"
    check_ping "$host" "public" "$dest" &
    sleep $RATE_LIMIT
    dest="${clusterip_arr[@]}"
    check_ping "$host" "cluster" "$dest" &
    sleep $RATE_LIMIT
done
wait
echo
pad_print '✓ '
echo 'Done'

print_header "Public"

# print column labels
for i in $(seq 0 $((hn_len - 1))); do
    printf "%${hn_len}s"
    for host in "${hostname_arr[@]}"; do
        pad_print "${host:$i:1}"
    done
    echo
done

# print results of public pings
for i in "${!hostname_arr[@]}"; do
    host="${hostname_arr[i]}"
    printf "%-12s" "$host"
    for j in "${!hostname_arr[@]}"; do
        if [[ i -eq j ]]; then
            pad_print '· '
            continue
        fi
        dest="${publicip_arr[j]}"
        pad_print "$(pass_fail "$host" "public" "$dest")"
    done
    echo
done


print_header "Cluster"

# print column labels
for i in $(seq 0 $((hn_len - 1))); do
    printf "%${hn_len}s"
    for host in "${hostname_arr[@]}"; do
        pad_print "${host:$i:1}"
    done
    echo
done

# print results of cluster pings
for i in "${!hostname_arr[@]}"; do
    host="${hostname_arr[i]}"
    printf "%-12s" "$host"
    for j in "${!hostname_arr[@]}"; do
        if [[ i -eq j ]]; then
            pad_print '· '
            continue
        fi
        dest="${clusterip_arr[j]}"
        pad_print "$(pass_fail "$host" "cluster" "$dest")"
    done
    echo
done
echo

rm -rf "$results_dir"
