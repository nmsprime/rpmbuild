#!/bin/bash
ip='localhost'
com='public'
warn=150
crit=100
max=400

while getopts ":H:C:w:c:" opt; do
	case $opt in
	H)
		ip="$OPTARG"
		;;
	C)
		com="$OPTARG"
		;;
	w)
		warn="$OPTARG"
		;;
	c)
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

tmp=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.1.4.1.5 | sed -s '/INTEGER: 0$/d')
idx=$(echo "$tmp" | cut -d'=' -f1 | awk -F'.' '{print $NF}')
val=$(echo "$tmp" | awk -F':' '{print $NF}' | sed 's/^ //')
name=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.1 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
alias=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.18 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
freq=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.1.2.1.2 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/$/\/1000000/' | bc -l | sed 's/\.\?0\+$//')

exit=0
status='OK'
text=''
while IFS=';' read -r -a line; do
	if [ ${line[3]} -lt $warn -a $status = 'OK' ]; then
		status='WARNING'
		exit=1
	fi
	if [ ${line[3]} -lt $crit -a $status = 'WARNING' ]; then
		status='CRITICAL'
		exit=2
	fi
	text+=" '${line[0]} (${line[1]}, ${line[2]} MHz)'=${line[3]};$warn;$crit;0;$max"
done < <(paste -d';' <(echo "$alias") <(echo "$name") <(echo "$freq") <(echo "$val"))

echo "US_SNR $status|$text"
exit $exit
