Name: genieacs-sim
Version: 0.0.1
Release: 1
Summary: TR-069 client simulator for GenieACS

Group: Applications/Communications
License: MIT
URL: https://github.com/genieacs/genieacs-sim

BuildRequires: gcc-c++, libxml2, npm
Requires: nodejs

%description
TR-069 client simulator for GenieACS

%install
CACHE_DIR=$(mktemp -d)
npm install %{name} --cache "$CACHE_DIR" --loglevel warn --global true --prefix %{buildroot}
rm -rf "$CACHE_DIR"
find %{buildroot} -name *.json -exec sed -i "s|%{buildroot}||g" {} +
find %{buildroot} -name *.gypi -exec sed -i "s|%{buildroot}||g" {} +
find %{buildroot} -name Makefile -exec sed -i "s|%{buildroot}||g" {} +

%files
/bin/*
/lib/*
#%{_unitdir}/*
#%config(noreplace) /lib/node_modules/genieacs/config/config.json

%changelog
* Thu Apr 01 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
