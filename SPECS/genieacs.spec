Name: genieacs
Version: 1.2.9
Release: 1
Summary: A fast and lightweight TR-069 Auto Configuration Server (ACS)

Group: Applications/Communications
License: AGPLv3
URL: https://%{name}.com/

BuildRequires: npm
Requires: mongodb-org-server, nodejs

%description
GenieACS is an open source TR-069 remote management solution with advanced
device provisioning capabilities.

%build
for service in cwmp fs nbi ui; do
cat << EOF > %{name}-${service}.service
[Unit]
Description=GenieACS ${service^^}
After=network.target

[Service]
User=nobody
EnvironmentFile=%{_sysconfdir}/%{name}/%{name}.env
ExecStart=/bin/%{name}-${service}
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
DEBUG=false
DEBUG_FILE=/var/log/genieacs/genieacs-debug.yaml
DEBUG_FORMAT=yaml
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
cache=$(mktemp -d)
npm install %{name}@%{version} -g --cache "${cache}" --prefix %{buildroot}
rm -rf "${cache}"
find %{buildroot} -name *.json -exec sed -i "s|%{buildroot}||g" {} +

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
/bin/*
%config(noreplace) %attr(600, nobody, nobody) %{_sysconfdir}/%{name}/%{name}.env
%config(noreplace) %attr(644, root, root) %{_sysconfdir}/logrotate.d/%{name}
/lib/*
%{_unitdir}/*.service
%attr(755, nobody, nobody) %{_datadir}/%{name}/ext
%attr(755, nobody, nobody) %{_localstatedir}/log/%{name}

%changelog
* Tue Aug 08 2023 Christian Schramm <christian.schramm@nmsprime.com> - 1.2.9-1
- Update to 1.2.9-1
- Change Dependency from rh-node12 to nodejs (nodejs 16 LTS)

* Mon Nov 08 2021 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.8-1
- Update to 1.2.8-1

* Sun Dec 13 2020 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.3-2
- Use master to workaround factory reset loop

* Tue Dec 08 2020 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.3-1
- Update to 1.2.3-1

* Wed May 29 2019 Ole Ernst <ole.ernst@nmsprime.com> - 1.1.3-1
- Initial RPM release
