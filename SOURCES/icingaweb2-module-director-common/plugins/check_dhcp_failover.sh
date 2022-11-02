#!/bin/bash

# Standard Nagios return codes
let OK=0
let WARNING=1
let CRITICAL=2
let UNKNOWN=3

# check if failover is enabled
# grep exits with 0 there is a match and failover is enabled
# use cat-pipe-grep because of entry in sudoers
_=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/dhcpd.conf | /usr/bin/grep -e '^\s*include.*failover\.conf')
CODE=$?
if [ $CODE -eq 1 ]; then
	echo "DHCPd failover not enabled; skipping check."
	exit $OK
elif [ $CODE -ne 0 ]; then
	echo "Error in checking if failover is enabled."
	exit $UNKNOWN
fi

# use cat-pipe-grep because of entry in sudoers
LOCALSTATE=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/check-failover.cmd | /usr/bin/omshell | /usr/bin/grep local-state | cut -d' ' -f 3)
PARTNERSTATE=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/check-failover.cmd | /usr/bin/omshell | /usr/bin/grep partner-state | cut -d' ' -f 3)

let GLOBALSTATE=$OK
echo "Local   state: $LOCALSTATE"
echo "Partner state: $PARTNERSTATE"

for STATE in $LOCALSTATE $PARTNERSTATE ; do
	# states are described in dhcpd.8 man page:
	# 1   - startup
	# 2   - normal
	# 3   - communications interrupted
	# 4   - partner down
	# 5   - potential conflict
	# 6   - recover
	# 7   - paused
	# 8   - shutdown
	# 9   - recover done
	# 10  - resolution interrupted
	# 11  - conflict done
	# 254 - recover wait
	case $STATE in
		00:00:00:02)
			;;
		00:00:00:01 | 00:00:00:05 | 00:00:00:06 | 00:00:00:11)
			if [ $GLOBALSTATE -eq $OK ]; then
				let GLOBALSTATE=$WARNING
			fi
			;;
		00:00:00:03 | 00:00:00:04 | 00:00:00:07 | 00:00:00:08 | 00:00:00:10 | 00:00:00:254)
			let GLOBALSTATE=$CRITICAL
			;;
		*)
			if [ $GLOBALSTATE -ne $CRITICAL ]; then
				let GLOBALSTATE=$UNKNOWN
			fi
			;;
	esac
done

exit $GLOBALSTATE
