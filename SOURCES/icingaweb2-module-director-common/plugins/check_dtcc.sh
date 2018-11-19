#!/bin/bash
ip='localhost'
com='public'

while getopts ":H:C:" opt; do
	case $opt in
	H)
		ip="$OPTARG"
		;;
	C)
		com="$OPTARG"
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

# get all inventory oids
inv=$(snmpwalk -Oqn -c "$com" -v2c "$ip" .1.3.6.1.2.1.47.1.1.1.1.3)

# search for cevChassisUbr10012
grep -q ".1.3.6.1.4.1.9.12.3.1.3.183$" <<< "$inv"
if [ $? -ne 0 ]; then
	echo "OK - no uBR10012 chassis"
	exit 0
fi

# get all DTCC modules
dtccs=$(grep "1.3.6.1.4.1.9.12.3.1.9.27.44$" <<< "$inv")
num=$(wc -l <<< "$dtccs")

if [ "$num" -lt 2 ]; then
	echo "CRITICAL - less then 2 DTCC modules plugged in"
	exit 2
fi

# get all serial numbers
ser=$(snmpwalk -Oqn -c "$com" -v2c "$ip" .1.3.6.1.2.1.47.1.1.1.1.11)

err=0
# iterate over all cevUbrDtcc
while read -r idx; do
	if grep ".1.3.6.1.2.1.47.1.1.1.1.11.$idx " <<< "$ser" | grep -q '""'; then
		# serial number not available means dtcc is broken
		((err++))
	fi
done <<< "$(cut -d ' ' -f1 <<< "$dtccs" | awk -F. '{print $NF}')"

if [ "$err" -gt 0 ]; then
	echo "CRITICAL - $err of $num DTCC modules broken"
	exit 2
fi

echo "OK"
exit 0
