#!/bin/bash
ip='localhost'
com='public'

while getopts ":H:C:w:c:" opt; do
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

crit=$(snmpwalk -Oqv -v2c -c "$com" "$ip" 1.3.6.1.4.1.9.9.138.1.2.1)
major=$(snmpwalk -Oqv -v2c -c "$com" "$ip" 1.3.6.1.4.1.9.9.138.1.2.2)
minor=$(snmpwalk -Oqv -v2c -c "$com" "$ip" 1.3.6.1.4.1.9.9.138.1.2.3)

# ciscoUbr7225Vxr reports unused GBICs as missing
if [ $(snmpwalk -Oqv -v2c -c "$com" "$ip" .1.3.6.1.2.1.1.2) = 'SNMPv2-SMI::enterprises.9.1.827' ]; then
	sub=$(snmpwalk -v2c -c "$com" "$ip" .1.3.6.1.4.1.9.9.138.1.2.5.1.2 | grep -e '\.7 =' -e '\.10 =' -e '\.13 =' | wc -l)
	crit=$((crit-sub))
fi

exit=0
status='OK'
text=''

if [ $major -gt 0 -o $minor -gt 0 ]; then
	status='WARNING'
	exit=1
fi
if [ $crit -gt 0 ]; then
	status='CRITICAL'
	exit=2
fi

echo "FACILITY_ALARM $status| critical=$crit major=$major minor=$minor"
exit $exit
