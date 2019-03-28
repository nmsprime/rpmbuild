#!/bin/bash
conf='/etc/dhcp/dhcpd.conf'
lease='/var/lib/dhcpd/dhcpd.leases'
warn=80
crit=90
ignore=15

while getopts ":c:l:W:C:I:" opt; do
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
	I)
		ignore="$OPTARG"
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

exit=0
status='OK'
text=''
for file in /etc/dhcp-nmsprime/cmts_gws/*.conf; do
	dir=$(mktemp -d)
	net=$(grep shared-network "$file" | cut -d'"' -f2)
	while read subnet; do
		read -r -a pool <<< "$subnet"
		awk "/${pool[1]} /,/${pool[2]} /" <<< "$pools" >> "$dir/${pool[0]}"
	done < <(grep -o "#pool:.*" "$file" | cut -d' ' -f2-4)

	for file in "$dir"/*; do
		read -r -a stats < <(awk '{all+=$5; used+=$6} END{printf("%.0f %d %d", used/all*100, all-used, all);}' "$file")

		if [ ${stats[1]} -lt $ignore ]; then
			if [ ${stats[0]} -gt $warn -a $status = 'OK' ]; then
				status='WARNING'
				exit=1
			fi
			if [ ${stats[0]} -gt $crit ]; then
				status='CRITICAL'
				exit=2
			fi

			text+=" '$net ($(basename "$file"), #left: ${stats[1]}/${stats[2]})'=${stats[0]}%;$warn;$crit"
		fi
	done
	rm -rf "$dir"
done

echo "$status |$text"
exit $exit
