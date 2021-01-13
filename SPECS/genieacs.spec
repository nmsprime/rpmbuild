Name: genieacs
Version: 1.2.3
Release: 2
Summary: A fast and lightweight TR-069 Auto Configuration Server (ACS)

Group: Applications/Communications
License: AGPLv3
URL: https://%{name}.com/
Source: https://github.com/%{name}/%{name}/archive/%{name}-%{version}.tar.gz

BuildRequires: rh-nodejs12-npm
Requires: mongodb-org-server, rh-nodejs12

%description
GenieACS is an open source TR-069 remote management solution with advanced
device provisioning capabilities.

%prep
%setup

%build
source /opt/rh/rh-nodejs12/enable
#sed -i 's/sessionContext\.provisions\.length/false/' lib/cwmp.ts
cache=$(mktemp -d)
npm install --cache "${cache}"
npm run build --cache "${cache}"
rm -rf "${cache}"

for service in cwmp fs nbi ui; do
cat << EOF > %{name}-${service}.service
[Unit]
Description=GenieACS ${service^^}
After=network.target

[Service]
User=nobody
EnvironmentFile=%{_sysconfdir}/%{name}/%{name}.env
ExecStart=/usr/bin/scl enable rh-nodejs12 '/lib/node_modules/genieacs/bin/%{name}-${service}'
Restart=always

[Install]
WantedBy=default.target
EOF
echo "${service^^}_ACCESS_LOG_FILE=%{_localstatedir}/log/%{name}/%{name}-${service}-access.log" >> %{name}.env
done

cat << EOF >> %{name}.env
CWMP_INTERFACE=localhost
CWMP_PORT=7548
FORWARDED_HEADER=127.0.0.1
NBI_INTERFACE=localhost
UI_INTERFACE=localhost
UI_JWT_SECRET=secret
EXT_DIR=%{_datadir}/%{name}/ext
EOF

sed -i "s/^/$(echo %{name} | tr '[:lower:]' '[:upper:]')_/" %{name}.env

cat << EOF >> %{name}.log
%{_localstatedir}/log/%{name}/*.log %{_localstatedir}/log/%{name}/*.yaml {
    daily
    rotate 30
    compress
    delaycompress
    dateext
}
EOF

%install
install -d %{buildroot}/lib/node_modules
mv dist %{buildroot}/lib/node_modules/%{name}
mv node_modules %{buildroot}/lib/node_modules/%{name}

for service in cwmp fs nbi ui; do
  install -D -m 644 %{name}-${service}.service %{buildroot}%{_unitdir}/%{name}-${service}.service
  rm %{name}-${service}.service
done

install -D -m 600 %{name}.env %{buildroot}%{_sysconfdir}/%{name}/%{name}.env
rm %{name}.env

install -D -m 644 %{name}.log %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
rm %{name}.log

install -d %{buildroot}%{_localstatedir}/log/%{name}
install -d %{buildroot}%{_datadir}/%{name}/ext

%files
%config(noreplace) %attr(600, nobody, nobody) %{_sysconfdir}/%{name}/%{name}.env
%{_sysconfdir}/logrotate.d/%{name}
/lib/node_modules/%{name}/*
%{_unitdir}/*.service
%attr(755, nobody, nobody) %{_datadir}/%{name}/ext
%attr(755, nobody, nobody) %{_localstatedir}/log/%{name}

%changelog
* Sun Dec 13 2020 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.3-2
- Use master to workaround factory reset loop
* Tue Dec 08 2020 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.3-1
- Update to 1.2.3-1
* Wed May 29 2019 Ole Ernst <ole.ernst@nmsprime.com> - 1.1.3-1
- Initial RPM release
