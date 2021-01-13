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

pools=$(dhcpd-pools -c "$conf" -l "$lease" -L 01 -f csv | tr -d '"')

exit=0
status='OK'
text=''
for file in /etc/dhcp-nmsprime/cmts_gws/*.conf; do
	dir=$(mktemp -d)
	net=$(grep shared-network "$file" | cut -d'"' -f2)
	while read subnet; do
		read -r -a pool <<< "$subnet"
		# filter for start and stop IP and get rid of net name,
		# which may contain a colon or double-quoting, making csv parsing harder
		grep -o "${pool[1]},${pool[2]}.*" <<< "$pools" >> "$dir/${pool[0]}"
	done < <(grep -o "#pool:.*" "$file" | cut -d' ' -f2-4)

	for file in "$dir"/*; do
		# skip if folder is empty
		[ -f "$file" ] || continue

		read -r -a stats < <(awk -F',' '{all+=$3; used+=$4} END{printf("%.0f %d %d", used/all*100, all-used, all);}' "$file")

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
