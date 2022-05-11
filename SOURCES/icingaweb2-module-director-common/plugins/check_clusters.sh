#!/bin/bash
dir='/run/nmsprime/icinga2'

if [ ! "$1" = 'outage' -a ! "$1" = 'proactive' -o "$#" -ne 2 ]; then
  exit 2
fi

output="$(grep -m1 "^[^|]*|'$2_single" "$dir/$1.csv")"

if [ -z "$output" ]; then
  echo "OK|'$2'=0;0;0;0;0"
  exit 0
else
  echo "$output"
fi

if [[ "$output" =~ ^CRITICAL ]]; then
  exit 2
fi

if [[ "$output" =~ ^WARNING ]]; then
  exit 1
fi

exit 0
