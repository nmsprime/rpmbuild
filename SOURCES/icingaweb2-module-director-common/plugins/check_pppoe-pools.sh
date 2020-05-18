#!/bin/bash
warn=80
crit=90
ignore=15

sec=$(awk '/\[nmsprime\]/{flag=1;next}/\[/{flag=0}flag' /etc/icingaweb2/resources.ini)
name=$(grep 'dbname' <<< "$sec" | cut -d'=' -f2 | tr -d "\"'" | xargs)
user=$(grep 'username' <<< "$sec" | cut -d'=' -f2 | tr -d "\"'" | xargs)
pw=$(grep 'password' <<< "$sec" | cut -d'=' -f2 | tr -d "\"'" | xargs)

exit=0
status='OK'
text=''
for pool in CPEPriv CPEPub; do
	read -r -a stats < <(mysql --batch "$name" -u "$user" --password="$pw" -e "SELECT ROUND(COUNT(expiry_time) / COUNT(*) * 100), COUNT(*) - COUNT(expiry_time), COUNT(*) FROM radippool WHERE pool_name = '$pool'" | tail -n +2)
	if [ ${stats[1]} -lt $ignore ]; then
		if [ ${stats[0]} -gt $warn -a $status = 'OK' ]; then
			status='WARNING'
			exit=1
		fi
		if [ ${stats[0]} -gt $crit ]; then
			status='CRITICAL'
			exit=2
		fi

		text+=" '$pool ($(hostname), #left: ${stats[1]}/${stats[2]})'=${stats[0]}%;$warn;$crit"
	fi
done

echo "$status |$text"
exit $exit
