Name: genieacs
Version: 1.1.3
Release: 1
Summary: A fast and lightweight TR-069 Auto Configuration Server (ACS)

Group: Applications/Communications
License: AGPLv3
URL: https://genieacs.com/

BuildRequires: gcc-c++, libxml2, npm
Requires: mongodb-server, nodejs

%description
GenieACS is an open source TR-069 remote management solution with advanced
device provisioning capabilities.

%build
for service in cwmp fs nbi; do
cat << EOF > genieacs-${service}.service
[Unit]
Description=GenieACS $(echo $service | tr '[a-z]' '[A-Z]')
After=network.target

[Service]
User=nobody
ExecStart=/bin/genieacs-$service
Restart=always

[Install]
WantedBy=default.target
EOF
done

%install
CACHE_DIR=$(mktemp -d)
npm install %{name} --cache "$CACHE_DIR" --loglevel warn --global true --prefix %{buildroot}
rm -rf "$CACHE_DIR"
find %{buildroot} -name *.json -exec sed -i "s|%{buildroot}||g" {} +
find %{buildroot} -name *.gypi -exec sed -i "s|%{buildroot}||g" {} +
find %{buildroot} -name Makefile -exec sed -i "s|%{buildroot}||g" {} +

for service in cwmp fs nbi; do
  install -D -m 644 genieacs-${service}.service %{buildroot}%{_unitdir}/genieacs-${service}.service
done

%files
/bin/*
/lib/*
%{_unitdir}/*
%config(noreplace) /lib/node_modules/genieacs/config/config.json

# https://gist.github.com/AfroThundr3007730/e30fcb2fd9cf60365b21e34170b98199
# systemctl start mongod
# systemctl enable mongod
# genieacs-cwmp

%changelog
* Wed May 29 2019 Ole Ernst <ole.ernst@nmsprime.com> - 1.1.3-1
- Initial RPM release
