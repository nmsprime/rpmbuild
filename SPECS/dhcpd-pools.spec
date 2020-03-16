Name: dhcpd-pools
Version: 2.28
Release: 1
Summary: ISC dhcpd leases usage analysis

Group: Applications/Communications
License: BSD
URL: https://sourceforge.net/projects/dhcpd-pools
Source: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.xz

BuildRequires: uthash-devel

%description
This is dhcpd-pools - ISC dhcpd lease status utility.

%prep
%autosetup

%build
%configure
make %{?_smp_mflags}

%install
#install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}
%make_install

%files
%{_bindir}/%{name}
%{_datarootdir}/%{name}/%{name}.cgi
%{_datarootdir}/%{name}/nagios.conf
%{_datarootdir}/%{name}/snmptest.pl
%{_mandir}/man1/%{name}.1.gz

%changelog
* Fri Aug 25 2017 Ole Ernst <ole.ernst@roetzer-engineering.com> - 2.28-1
- Initial RPM release
