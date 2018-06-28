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

if [ $(snmpget -Oqv -v1 -c "$com" "$ip" .1.3.6.1.4.1.6437.1.3.3.2.1.0) -eq '2' ]; then
	echo "ORA STATUS: Critical ALSC RED ALARM"
	exit 2
fi

if [ $(snmpget -Oqv -v1 -c "$com" "$ip" .1.3.6.1.4.1.6437.1.3.3.2.2.0) -eq '3' ]; then
	echo "ORA STATUS: Warning ALSC Limit"
	exit 1
fi

echo "ORA STATUS: okay"
exit 0
