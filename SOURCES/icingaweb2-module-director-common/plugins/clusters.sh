#!/bin/bash

if [ "$1" = "online" ]; then
  output=$(grep "$2" /run/nmsprime/icinga2/clusters_online.csv)
elif [ "$1" = "power" ]; then
  output=$(grep "$2" /run/nmsprime/icinga2/clusters_power.csv)
else
  exit 2
fi

echo "$output"

if [ $(echo $output | cut -d'|' -f1) = "CRITICAL" ]; then
  exit 2
fi

if [ $(echo $output | cut -d'|' -f1) = "WARNING" ]; then
  exit 1
fi

exit 0
