#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
	echo "Usage: $0 SPECS/<specfile>" >&2
	exit 1
fi
SPEC="$1"

# Active LTS major for GenieACS / nodejs-axios RPMs (Maintenance LTS fallback: 22).
# Version installed at the build machine Needs to be the same version as in the .spec files
NODE_LTS_MAJOR=24

cd "$(dirname "$0")"

spec_needs_nodejs_lts() {
	case "$SPEC" in
		SPECS/genieacs.spec | SPECS/nodejs-axios*.spec)
			return 0
			;;
		*)
			return 1
			;;
	esac
}

node_major_version() {
	if ! command -v node >/dev/null 2>&1; then
		echo 0
		return
	fi
	local ver="${1:-$(node -v)}"
	ver="${ver#v}"
	echo "${ver%%.*}"
}

ensure_nodejs_lts() {
	local major
	major=$(node_major_version)

	if [ "$major" -eq "$NODE_LTS_MAJOR" ]; then
		echo "Node.js $(node -v) OK for build (Active LTS ${NODE_LTS_MAJOR}.x)." >&2
		return 0
	fi

	echo "ERROR: ${SPEC} requires Node.js ${NODE_LTS_MAJOR}.x (Active LTS)." >&2
	if [ "$major" -gt 0 ]; then
		echo "  Found: $(node -v)" >&2
	fi
	echo "  Fallback if runtime issues appear on staging: nodejs:22 (Maintenance LTS, Requires >= 22 and < 23)." >&2

	if [ "$(id -u)" -eq 0 ] && command -v dnf >/dev/null 2>&1; then
		echo "Attempting dnf module switch to nodejs:${NODE_LTS_MAJOR}..." >&2
		dnf -y module reset nodejs
		dnf -y module enable "nodejs:${NODE_LTS_MAJOR}"
		dnf -y module install "nodejs:${NODE_LTS_MAJOR}/common"
		dnf -y install npm

		major=$(node_major_version)
		if [ "$major" -eq "$NODE_LTS_MAJOR" ]; then
			echo "Node.js $(node -v) ready." >&2
			return 0
		fi
	fi

	echo "On the build host run:" >&2
	echo "  sudo dnf -y module reset nodejs" >&2
	echo "  sudo dnf -y module enable nodejs:${NODE_LTS_MAJOR}" >&2
	echo "  sudo dnf -y module install nodejs:${NODE_LTS_MAJOR}/common" >&2
	echo "  sudo dnf -y install npm" >&2
	exit 1
}

if spec_needs_nodejs_lts; then
	ensure_nodejs_lts
fi

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
