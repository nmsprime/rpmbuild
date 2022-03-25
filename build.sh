#!/bin/bash
if [ $# -ne 1 ]; then
	echo "Usage: $0 SPECS/<specfile>" >&2
	exit 1
fi
SPEC="$1"

cd "$(dirname "$0")"

for FOLDER in BUILD BUILDROOT SOURCES; do
	rm -rf "$FOLDER"
	git checkout "$FOLDER"
done

if [ "$SPEC" = 'SPECS/icingaweb2-module-director.spec' ]; then
	pushd SOURCES/icingaweb2-module-director-common
	tar cvf ../icingaweb2-module-director-common.tar.gz .
	popd
fi

spectool -C SOURCES -g "$SPEC"

rpmbuild -ba "$SPEC"
