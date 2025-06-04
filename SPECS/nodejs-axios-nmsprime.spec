Name: nodejs-axios-nmsprime
Version: 1.6.8
Release: 1
Summary: Promise based HTTP client for the browser and node.js
Group: Applications/Communications
License: MIT
BuildArch: noarch
URL: https://github.com/axios/axios

BuildRequires: npm
Requires: nodejs

%description
Promise based HTTP client for the browser and node.js

%install
CACHE_DIR=$(mktemp -d)
npm install axios --cache "$CACHE_DIR" --loglevel warn --global true --prefix %{buildroot}
rm -rf "$CACHE_DIR"

%files
/lib/node_modules/axios/*

%changelog
* Wed Apr 24 2024 Ole Ernst <ole.ernst@nmsprime.com> - 1.6.8-1
- Initial RPM release
