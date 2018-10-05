#!/bin/bash
pkg='nmsprime-base'

rpm -q $pkg > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
	echo 'OK: nmsprime not installed via rpm'
	exit 0
fi

yum check-update $pkg > /dev/null 2>&1
ret=$?

if [[ $ret -eq 100 ]]; then
	echo 'CRITICAL: nmsprime updates available'
	exit 2
fi

if [[ $ret -eq 1 ]]; then
	echo 'WARNING: an error occured while checking for nmsprime updates'
	exit 1
fi

echo 'OK: no nmsprime updates available'
exit 0
