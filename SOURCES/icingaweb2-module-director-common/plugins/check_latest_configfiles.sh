#!/bin/bash
# see https://unix.stackexchange.com/a/356400

cd '/tftpboot'
for type in cm mta; do
	comm=$(comm -3 <(printf '%s\0' $type/$type-*.conf | xargs -r0 ls -1q | cut -d'.' -f1 | sort) <(printf '%s\0' $type/$type-*.cfg | xargs -r0 ls -1q | cut -d'.' -f1 | sort))
	if [[ "$comm" ]]; then
		echo "CRITICAL - not all $type configfiles were generated:"
		echo "$comm"
		exit 2
	fi

	old=$(awk '$1 > $3 {print $2}' <(paste -d' ' <(printf '%s\0' $type/$type-*.conf | xargs -r0 stat -c '%Y %n') <(printf '%s\0' $type/$type-*.cfg | xargs -r0 stat -c '%Y %n')))
	if [[ "$old" ]]; then
		echo "CRITICAL - outdated $type configfiles:"
		echo "$old"
		exit 2
	fi
done

echo 'OK'
exit 0
