#!/bin/bash

if [ "$1" = "outage" ]; then
  output=$(grep "$2" /run/nmsprime/icinga2/outage.csv)
elif [ "$1" = "proactive" ]; then
  output=$(grep "$2" /run/nmsprime/icinga2/proactive.csv)
elif [ "$1" = "outage_all" ]; then
  output=$(grep "^[[:alpha:]]*|'$2" /run/nmsprime/icinga2/outage_all.csv)
elif [ "$1" = "proactive_all" ]; then
  output=$(grep "^[[:alpha:]]*|'$2" /run/nmsprime/icinga2/proactive_all.csv)
else
  exit 2
fi

echo "$output"

if [ $(echo $output | cut -d'|' -f1) = "CRITICAL" ]; then
  exit 2
elif [ $(echo $output | cut -d'|' -f1) = "WARNING" ]; then
  exit 1
else
  exit 0
fi
