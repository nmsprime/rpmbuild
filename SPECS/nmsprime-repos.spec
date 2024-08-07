Name: nmsprime-repos
Version: 4.0.0
Release: 3
Summary: NMS Prime and dependency RPM repos

Group: Applications/Communications
License: GPLv3
BuildArch: noarch
URL: https://www.nmsprime.com
Source1: https://rpms.remirepo.net/enterprise/remi-release-9.rpm
Source2: https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

%description
This package contains the nmsprime and dependency RPM repos.

%prep
rpm2cpio %{_sourcedir}/remi-release-9.rpm | cpio -ivdm
rpm2cpio %{_sourcedir}/pgdg-redhat-repo-latest.noarch.rpm | cpio -ivdm

%build
cat << EOF > nmsprime-os.repo
[nmsprime-os]
name=NMS Prime OS
baseurl=https://repo9.nmsprime.com/rpm/nmsprime-rocky/os
enabled=1
gpgcheck=0
sslverify=1
EOF

cat << EOF > nmsprime-prime.repo
[nmsprime-prime]
name=NMS Prime
baseurl=https://repo9.nmsprime.com/rpm/nmsprime-rocky/prime
enabled=0
gpgcheck=0
sslverify=1
EOF

cat << "EOF" > mongodb-org-7.0.repo
[mongodb-org-7.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/7.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc
EOF

cat << "EOF" > timescale_timescaledb.repo
[timescale_timescaledb]
name=timescale_timescaledb
baseurl=https://packagecloud.io/timescale/timescaledb/el/$releasever/$basearch
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/timescale/timescaledb/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

cat << EOF > grafana.repo
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
exclude=*beta*
EOF

cat << "EOF" > influxdb.repo
[influxdb]
name = InfluxDB Repository - RHEL
baseurl = https://repos.influxdata.com/rhel/$releasever/$basearch/stable/
enabled = 1
gpgcheck = 1
gpgkey = https://repos.influxdata.com/influxdb.key
EOF

%install
install -Dm 644 nmsprime-os.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime-os.repo
install -Dm 644 nmsprime-prime.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime-prime.repo
install -Dm 644 mongodb-org-7.0.repo %{buildroot}%{_sysconfdir}/yum.repos.d/mongodb-org-7.0.repo
install -Dm 644 timescale_timescaledb.repo %{buildroot}%{_sysconfdir}/yum.repos.d/timescale_timescaledb.repo
install -Dm 644 grafana.repo %{buildroot}%{_sysconfdir}/yum.repos.d/grafana.repo
install -Dm 644 influxdb.repo %{buildroot}%{_sysconfdir}/yum.repos.d/influxdb.repo
install -dm755 %{buildroot}%{_sysconfdir}/pki/rpm-gpg
mv etc/pki/rpm-gpg/* %{buildroot}%{_sysconfdir}/pki/rpm-gpg/
install -dm755 %{buildroot}%{_sysconfdir}/yum.repos.d
mv etc/yum.repos.d/* %{buildroot}%{_sysconfdir}/yum.repos.d/

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/*

%changelog
* Thu Mar 07 2024 Ole Ernst <ole.ernst@nmsprime.com> - 4.0.0-3
- adjust baseurl for rocky9 release

* Thu Mar 07 2024 Ole Ernst <ole.ernst@nmsprime.com> - 4.0.0-2
- Reintroduce remi repo for php-8.2 support
- Update PostgreSQL repository
- Update MongoDB repository
- Remove alma-devel repo, since we can get freeradius-postgresql from CRB

* Fri Nov 10 2023 Ole Ernst <ole.ernst@nmsprime.com> - 4.0.0-1
- Add alma-devel repo used for freeradius-postgresql
- Add influxdb repo used for telegraf
- Remove unneeded remi repo, since native php is used from now on

* Mon Apr 24 2023 Christian Schramm <christian.schramm@nmsprime.com> - 3.2.0-1
- Add Telegraf repositories
- Update Grafana repo urls

* Wed Oct 27 2021 Christian Schramm <christian.schramm@nmsprime.com> - 3.1.0-1
- Add PHP 8 repositories

* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-2
- Add Grafana, Icinga, Postgresql, TimescaleDB repositories

* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-1
- Initial RPM release
