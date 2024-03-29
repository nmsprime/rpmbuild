Name: modempoller-nmsprime
Version: 0.0.3
Release: 3
Summary: A highly efficient modem snmp poller

Group: Applications/Communications
License: GPLv3
URL: https://github.com/nmsprime/async-snmp-poller
Source: https://raw.githubusercontent.com/nmsprime/async-snmp-poller/master/src/%{name}.c

Requires: net-snmp-libs libpq5
BuildRequires: gcc net-snmp-devel libpq5-devel

%description
This asynchronous snmp poller solves the issue with Cacti when monitoring several
thousand devices. Cacti produces a massive CPU load and takes a long time to collect
its monitoring data by using hundreds of concurrent php workers which handle each a
small batch of devices sequentially. This blocks the CPU and scales pretty poorly.

%build
gcc -s -L $(pg_config --libdir) -l netsnmp -l pq -o %{name} %{_sourcedir}/%{name}.c

%install
install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Tue Dec 19 2023 Christian Schramm <christian.schramm@nmsprime.com> - 0.0.3-3
- Use host function to retreive ipv4

* Mon Mar 21 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 0.0.3-2
- Require Postgres DB now

* Wed Mar 09 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.3-1
- switch SQL client lib from MySQL to PostgreSQL

* Tue Aug 24 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.2-1
- Rebuild using nmsprime.modem rather than cacti.host

* Mon May 06 2019 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
