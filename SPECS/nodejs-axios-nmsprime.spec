Name: nodejs-axios-nmsprime
Version: 1.6.8
Release: 2
Summary: Promise based HTTP client for the browser and node.js
Group: Applications/Communications
License: MIT
BuildArch: noarch
URL: https://github.com/axios/axios

# Node.js 24 Active LTS (DNF module nodejs:24). EL9 modular RPMs need epoch in Requires:
#   nodejs >= 1:24, nodejs < 1:25  (plain "nodejs < 25" does not resolve in dnf builddep).
# Staging fallback if 24 fails: nodejs:22 with nodejs >= 1:22, nodejs < 1:23.
BuildRequires: nodejs >= 1:24, nodejs < 1:25, npm
Requires: nodejs >= 1:24, nodejs < 1:25

%description
Promise based HTTP client for the browser and node.js

%install
CACHE_DIR=$(mktemp -d)
npm install axios@%{version} --cache "$CACHE_DIR" --loglevel warn --global true --prefix %{buildroot}
rm -rf "$CACHE_DIR"

%files
/lib/node_modules/axios/*

%changelog
* Wed May 27 2026 NMS Prime <patrick.reichel@nmsprime.com> - 1.6.8-2
- Require Node.js 24.x Active LTS (>= 1:24, < 1:25); pin axios@%{version} at build time

* Wed Apr 24 2024 Ole Ernst <ole.ernst@nmsprime.com> - 1.6.8-1
- Initial RPM release
