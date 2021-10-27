#!/bin/bash

OK=0
WARNING=1
CRITICAL=2
SUPERVISORCTLSTATUSCMD='sudo /usr/bin/supervisorctl status'
RUNNINGSTATE="RUNNING"

# check if supervisord is active
/usr/bin/systemctl is-active --quiet supervisord.service
if [[ $? -ne 0 ]]; then
	echo 'CRITICAL: supervisord.service not running'
	exit $CRITICAL
fi

STATUS=$($SUPERVISORCTLSTATUSCMD)
# check for error (e.g. icinga not allow to sudo supervisorctl)
if [[ $? -ne 0 ]]; then
	echo "CRITICAL: Error in calling $SUPERVISORCTLSTATUSCMD"
	exit $CRITICAL
fi

# check if there are processes not in $RUNNINGSTATE state
NOTRUNNING=$(echo "$STATUS" | grep -v " $RUNNINGSTATE " | wc -l)
if [ "$NOTRUNNING" != "0" ]; then
	echo "CRITICAL: $NOTRUNNING supervisor processes not in state $RUNNINGSTATE; check '$SUPERVISORCTLSTATUSCMD' for details"
	exit $CRITICAL
fi

# check if there is at least one supervisor process running
RUNNING=$(echo "$STATUS" | grep " $RUNNINGSTATE " | wc -l)
if [ "$RUNNING" == "0" ]; then
	echo "WARNING: No supervisor processes in state $RUNNINGSTATE"
	exit $WARNING
fi

# all is fine :-)
echo "OK: $RUNNING processes in state $RUNNINGSTATE"
exit $OK
