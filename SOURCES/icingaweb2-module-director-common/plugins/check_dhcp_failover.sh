#!/bin/bash

# Standard Nagios return codes
let OK=0
let WARNING=1
let CRITICAL=2
let UNKNOWN=3

# states are described in dhcpd.8 man page:
# added in decimal and hex – seems to be hex in the answer (but every time??)
declare -A FAILOVER_STATES_DESCRIPTIONS
FAILOVER_STATES_DESCRIPTIONS[00:00:00:01]="startup"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:02]="normal"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:03]="communications interrupted"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:04]="partner down"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:05]="potential conflict"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:06]="recover"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:07]="paused"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:08]="shutdown"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:09]="recover done"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:10]="resolution interrupted"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:0a]="resolution interrupted"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:0A]="resolution interrupted"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:11]="conflict done"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:0b]="conflict done"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:0B]="conflict done"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:254]="recover wait"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:fe]="recover wait"
FAILOVER_STATES_DESCRIPTIONS[00:00:00:FE]="recover wait"

declare -A FAILOVER_STATES_RETURN_CODES
FAILOVER_STATES_RETURN_CODES[00:00:00:01]=$WARNING      # startup
FAILOVER_STATES_RETURN_CODES[00:00:00:02]=$OK           # normal
FAILOVER_STATES_RETURN_CODES[00:00:00:03]=$CRITICAL     # communications interrupted
FAILOVER_STATES_RETURN_CODES[00:00:00:04]=$CRITICAL     # partner down
FAILOVER_STATES_RETURN_CODES[00:00:00:05]=$WARNING      # potential conflict
FAILOVER_STATES_RETURN_CODES[00:00:00:06]=$WARNING      # recover
FAILOVER_STATES_RETURN_CODES[00:00:00:07]=$CRITICAL     # paused
FAILOVER_STATES_RETURN_CODES[00:00:00:08]=$CRITICAL     # shutdown
FAILOVER_STATES_RETURN_CODES[00:00:00:09]=$WARNING      # recover done
FAILOVER_STATES_RETURN_CODES[00:00:00:10]=$CRITICAL     # resolution interrupted
FAILOVER_STATES_RETURN_CODES[00:00:00:0a]=$CRITICAL     # resolution inerruptedt
FAILOVER_STATES_RETURN_CODES[00:00:00:0A]=$CRITICAL     # resolution inerruptedt
FAILOVER_STATES_RETURN_CODES[00:00:00:11]=$WARNING      # conflict done
FAILOVER_STATES_RETURN_CODES[00:00:00:0b]=$WARNING      # conflict done
FAILOVER_STATES_RETURN_CODES[00:00:00:0B]=$WARNING      # conflict done
FAILOVER_STATES_RETURN_CODES[00:00:00:254]=$WARNING     # recover wait
FAILOVER_STATES_RETURN_CODES[00:00:00:fe]=$WARNING      # recover wait
FAILOVER_STATES_RETURN_CODES[00:00:00:FE]=$WARNING      # recover wait


# check if failover is enabled – use cat-pipe-grep because of entry in sudoers
# grep exits with 0 there is a match and failover is enabled
_=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/dhcpd.conf | /usr/bin/grep -e '^\s*include.*failover\.conf')
CODE=$?
if [ $CODE -eq 1 ]; then
	echo "DHCPd failover not enabled; skipping check."
	exit $OK
elif [ $CODE -ne 0 ]; then
	echo "Error in checking if failover is enabled."
	exit $UNKNOWN
fi

LOCALSTATE=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/check-failover.cmd | /usr/bin/omshell | /usr/bin/grep local-state | cut -d' ' -f 3)
PARTNERSTATE=$(/usr/bin/sudo /usr/bin/cat /etc/dhcp-nmsprime/check-failover.cmd | /usr/bin/omshell | /usr/bin/grep partner-state | cut -d' ' -f 3)

# set to n/a if empty string
[ -z "$LOCALSTATE" ] && LOCALSTATE="n/a"
[ -z "$PARTNERSTATE" ] && PARTNERSTATE="n/a"

let GLOBALSTATE=$OK

# print own state
if [[ ${FAILOVER_STATES_DESCRIPTIONS[$LOCALSTATE]} ]]; then
    DESC=${FAILOVER_STATES_DESCRIPTIONS[$LOCALSTATE]}
else
    DESC="unknown"
fi
echo "Local   state: $LOCALSTATE ($DESC)"

# print peer's state
if [[ ${FAILOVER_STATES_DESCRIPTIONS[$PARTNERSTATE]} ]]; then
    DESC=${FAILOVER_STATES_DESCRIPTIONS[$PARTNERSTATE]}
else
    DESC="unknown"
fi
echo "Partner state: $PARTNERSTATE ($DESC)"

for STATE in $LOCALSTATE $PARTNERSTATE ; do

    if [[ ${FAILOVER_STATES_RETURN_CODES[$STATE]} ]]; then
        # state in array return the highest return code of both states
        if (( ${FAILOVER_STATES_RETURN_CODES[$STATE]} > $GLOBALSTATE )); then
            let GLOBALSTATE=${FAILOVER_STATES_RETURN_CODES[$STATE]}
        fi
    else
        # state not in array – return unknown if not critical is set
        if [ $GLOBALSTATE -ne $CRITICAL ]; then
            let GLOBALSTATE=$UNKNOWN
        fi
    fi

done

exit $GLOBALSTATE
