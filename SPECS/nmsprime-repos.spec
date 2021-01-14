Name: nmsprime-repos
Version: 2.6.0
Release: 1
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
baseurl=https://repo.nmsprime.com/rpm/nmsprime
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

%install
install -D -m 644 nmsprime.repo %{buildroot}%{_sysconfdir}/yum.repos.d/nmsprime.repo
install -D -m 644 mongodb-org-4.4.repo %{buildroot}%{_sysconfdir}/yum.repos.d/mongodb-org-4.4.repo
rm nmsprime.repo
rm mongodb-org-4.4.repo

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/yum.repos.d/*

%changelog
* Wed Jan 13 2021 Ole Ernst <ole.ernst@nmsprime.com> - 2.6.0-1
- Initial RPM release
