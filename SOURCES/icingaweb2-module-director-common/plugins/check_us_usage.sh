#!/bin/bash
ip='localhost'
com='public'
warn=70
crit=90

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

idx=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.1.4.1.5 | sed -s '/INTEGER: 0$/d' | cut -d'=' -f1 | awk -F'.' '{print $NF}' | sed 's/ $//')
val=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.3.9.1.3 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
if [ -z "$val" ]; then
	echo "US_USAGE not supported"
	exit 0
fi
name=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.1 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
alias=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.18 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
freq=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.1.2.1.2 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/$/\/1000000/' | bc -l | sed 's/\.\?0\+$//')

exit=0
status='OK'
text=''
while IFS=';' read -r -a line; do
	if [ ${line[3]} -gt $warn -a $status = 'OK' ]; then
		status='WARNING'
		exit=1
	fi
	if [ ${line[3]} -gt $crit -a $status = 'WARNING' ]; then
		status='CRITICAL'
		exit=2
	fi
	text+=" '${line[0]} (${line[1]}, ${line[2]} MHz)'=${line[3]}%;$warn;$crit"
done < <(paste -d';' <(echo "$alias") <(echo "$name") <(echo "$freq") <(echo "$val"))

echo "US_USAGE $status|$text"
exit $exit
