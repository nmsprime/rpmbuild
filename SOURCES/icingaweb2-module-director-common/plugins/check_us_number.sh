#!/bin/bash
ip='localhost'
com='public'
warn=70
crit=60

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
tot=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.4.1.9.9.116.1.4.1.1.3 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
act=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.4.1.9.9.116.1.4.1.1.5 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
name=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.1 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
alias=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.31.1.1.1.18 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/^ //')
freq=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.2.1.10.127.1.1.2.1.2 | grep -f <(echo "$idx") | awk -F':' '{print $NF}' | sed 's/$/\/1000000/' | bc -l | sed 's/\.\?0\+$//')

exit=0
status='OK'
text=''
while IFS=';' read -r -a line; do
	if [ "${line[3]}" -lt 15 -o "${line[4]}" -eq 0 ]; then
		continue
	fi
	ratio=$(echo "scale=2; 100*${line[3]}/${line[4]}" | bc -l)
	if [ $(echo "$ratio <= $warn" | bc) -eq 1 -a $status = 'OK' ]; then
		status='WARNING'
		exit=1
	fi
	if [ $(echo "$ratio <= $crit" | bc) -eq 1 -a $status = 'WARNING' ]; then
		status='CRITICAL'
		exit=2
	fi
	text+=" '${line[0]} (${line[1]}, ${line[2]} MHz)'=$ratio%;$warn;$crit"
done < <(paste -d';' <(echo "$alias") <(echo "$name") <(echo "$freq") <(echo "$act") <(echo "$tot"))

echo "US_NUMBER $status|$text"
exit $exit
