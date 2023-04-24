Name: nmsprime-repos
Version: 3.2.0
Release: 1
Summary: NMS Prime and dependency RPM repos

Group: Applications/Communications
License: GPLv3
BuildArch: noarch
URL: https://www.nmsprime.com
Source1: https://packages.icinga.com/epel/icinga-rpm-release-7-latest.noarch.rpm
Source2: https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm

%description
This package contains the nmsprime and dependency RPM repos.

%prep
rpm2cpio %{_sourcedir}/icinga-rpm-release-7-latest.noarch.rpm | cpio -ivdm
rpm2cpio %{_sourcedir}/pgdg-redhat-repo-latest.noarch.rpm | cpio -ivdm

%build
cat << EOF >> nmsprime-os.repo
[nmsprime-os]
name=NMS Prime
baseurl=https://repo.nmsprime.com/rpm/nmsprimeNG/os
enabled=1
gpgcheck=0
sslverify=1
EOF

cat << EOF >> nmsprime-prime.repo
[nmsprime-prime]
name=NMS Prime
baseurl=https://repo.nmsprime.com/rpm/nmsprimeNG/prime
enabled=0
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

cat << EOF > remi-safe.repo
[remi-safe]
name=Safe Remi's RPM repository for Enterprise Linux 7 - $basearch
mirrorlist=http://cdn.remirepo.net/enterprise/7/safe/mirror
enabled=1
gpgcheck=1
gpgkey=https://rpms.remirepo.net/RPM-GPG-KEY-remi
EOF

cat << EOF > influxdb.repo
[influxdb]
name = InfluxData Repository - Stable
baseurl = https://repos.influxdata.com/stable/\$basearch/main
enabled = 1
gpgcheck = 1
gpgkey = https://repos.influxdata.com/influxdata-archive_compat.key
EOF


%install
install -Dm 644 nmsprime-os.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime-os.repo
install -Dm 644 nmsprime-prime.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime-prime.repo
install -Dm 644 mongodb-org-4.4.repo %{buildroot}%{_sysconfdir}/yum.repos.d/mongodb-org-4.4.repo
install -Dm 644 timescale_timescaledb.repo %{buildroot}%{_sysconfdir}/yum.repos.d/timescale_timescaledb.repo
install -Dm 644 grafana.repo %{buildroot}%{_sysconfdir}/yum.repos.d/grafana.repo
install -Dm 644 remi-safe.repo %{buildroot}%{_sysconfdir}/yum.repos.d/remi-safe.repo
install -Dm 644 ./etc/yum.repos.d/pgdg-redhat-all.repo %{buildroot}%{_sysconfdir}/yum.repos.d/pgdg-redhat-all.repo
install -Dm 644 ./etc/yum.repos.d/ICINGA-release.repo %{buildroot}%{_sysconfdir}/yum.repos.d/ICINGA-release.repo
install -Dm 644 ./etc/pki/rpm-gpg/RPM-GPG-KEY-ICINGA %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-ICINGA
install -Dm 644 ./etc/pki/rpm-gpg/RPM-GPG-KEY-PGDG %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-PGDG

rm nmsprime-os.repo
rm nmsprime-prime.repo
rm mongodb-org-4.4.repo
rm timescale_timescaledb.repo
rm grafana.repo
rm remi-safe.repo
rm -rf ./etc
rm -rf ./usr

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/*

%changelog
* Mon Apr 24 2023 Christian Schramm <christian.schramm@nmsprime.com> - 3.2.0-1
- Add Telegraf repositories

* Wed Oct 27 2021 Christian Schramm <christian.schramm@nmsprime.com> - 3.1.0-1
- Add PHP 8 repositories

* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-2
- Add Grafana, Icinga, Postgresql, TimescaleDB repositories

* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 3.0.0-1
- Initial RPM release
