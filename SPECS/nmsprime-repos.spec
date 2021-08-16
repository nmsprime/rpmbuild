Name: nmsprime-repos
Version: 3.0.0
Release: 2
Summary: NMS Prime and dependency RPM repos

Group: Applications/Communications
License: GPLv3
BuildArch: noarch
URL: https://www.nmsprime.com

%description
This package contains the nmsprime and dependency RPM repos.

%prep

%build
cat << EOF >> nmsprime.repo
[nmsprime]
name=NMS Prime
baseurl=https://repo.nmsprime.com/rpm/nmsprimeOS
enabled=1
gpgcheck=0
sslverify=1
EOF

cat << "EOF" >> mongodb-org-4.4.repo
[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
EOF

cat << "EOF" >> timescale_timescaledb.repo
[timescale_timescaledb]
name=timescale_timescaledb
baseurl=https://packagecloud.io/timescale/timescaledb/el/$releasever/$basearch
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/timescale/timescaledb/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
EOF

cat << EOF > grafana.repo
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

%install
install -D -m 644 nmsprime.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime.repo
install -D -m 644 mongodb-org-4.4.repo %{buildroot}%{_sysconfdir}/yum.repos.d/mongodb-org-4.4.repo
install -D -m 644 timescale_timescaledb.repo %{buildroot}%{_sysconfdir}/yum.repos.d/timescale_timescaledb.repo
install -D -m 644 grafana.repo %{buildroot}%{_sysconfdir}/yum.repos.d/grafana.repo
rm nmsprime.repo
rm mongodb-org-4.4.repo
rm timescale_timescaledb.repo
rm grafana.repo

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/yum.repos.d/*

%changelog
* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-2
- Add TimescaleDB and Grafana repositories

* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-1
- Initial RPM release
