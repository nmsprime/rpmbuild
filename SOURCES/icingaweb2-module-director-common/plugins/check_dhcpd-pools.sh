#!/bin/bash
conf='/etc/dhcp/dhcpd.conf'
lease='/var/lib/dhcpd/dhcpd.leases'
warn=10
crit=5

while getopts ":c:l:W:C:" opt; do
	case $opt in
	c)
		conf="$OPTARG"
		;;
	l)
		lease="$OPTARG"
		;;
	W)
		warn="$OPTARG"
		;;
	C)
		crit="$OPTARG"
		;;
	\?)
		echo "Invalid option: -$OPTARG" >&2
		exit 2
		;;
	:)
		echo "Option -$OPTARG requires an argument." >&2
		exit 2
		;;
	esac
done

pools=$(dhcpd-pools -c "$conf" -l "$lease" | sed -e '1,2d' -e '/ETHERNET/d' -e '/^$/q' | sed '/^$/d')
sh_nets=$(echo "$pools" | cut -d' ' -f1 | sort -u)

exit=0
status='OK'
text=''
for net in $sh_nets; do
	prefixes=$(echo "$pools" | grep "$net" | awk '{print $2}' | cut -d'.' -f1 | sort -u)

	for prefix in $prefixes; do
		used=0
		all=0
		IFS=$'\n'
		for subnet in $(echo "$pools" | grep "$net[[:space:]]\+$prefix\."); do
			all=$(echo "$subnet" | awk -v all="$all" '{print $5+all}')
			used=$(echo "$subnet" | awk -v used="$used" '{print $6+used}')
		done
		left=$(($all - used))

		if [ $left -le $warn -a $status = 'OK' ]; then
			status='WARNING'
			exit=1
		fi
		if [ $left -le $crit ]; then
			status='CRITICAL'
			exit=2
		fi

		text+=" '$net ($prefix.x, #left: $left/$all)'=$used;$((all - warn));$((all - crit));0;$all"
	done
done

echo "$status |$text"
exit $exit
