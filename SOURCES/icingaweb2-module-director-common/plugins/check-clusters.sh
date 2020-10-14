#!/bin/bash

if [ "$1" = "outage" ]; then
  output=$(grep "^[[:alpha:]]*|'$2" /run/nmsprime/icinga2/outage.csv)
elif [ "$1" = "proactive" ]; then
  output=$(grep "^[[:alpha:]]*|'$2" /run/nmsprime/icinga2/proactive.csv)
else
  exit 2
fi

if [ -z "$output" ]; then
  echo "OK|'$2'=0;0;0;0;0"
  exit 0
else
  echo "$output"
fi

if [ $(echo $output | cut -d'|' -f1) = "CRITICAL" ]; then
  exit 2
elif [ $(echo $output | cut -d'|' -f1) = "WARNING" ]; then
  exit 1
else
  exit 0
fi
