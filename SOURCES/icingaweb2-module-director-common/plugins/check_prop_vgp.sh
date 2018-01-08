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

if [ $(snmpget -O qv -v1 -c $com $ip .1.3.6.1.4.1.6437.1.2.2.2.1.0) -eq '2' ]; then
	echo "VGP STATUS: Critical ALSC RED ALARM"
	exit 2
fi

if [ $(snmpget -O qv -v1 -c $com $ip .1.3.6.1.4.1.6437.1.2.2.2.2.0) -eq '3' ]; then
	echo "VGP STATUS: Warning ALSC Limit"
	exit 1
fi

if [ $(snmpget -O qv -v1 -c $com $ip .1.3.6.1.4.1.6437.1.2.2.3.13.0) -eq '1' ]; then
	echo "VGP STATUS: Warning No auto adjustment"
	exit 1
fi

echo "VGP STATUS: okay"
exit 0
