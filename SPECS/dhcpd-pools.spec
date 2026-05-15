Name: dhcpd-pools
Version: 3.2
Release: 1
Summary: ISC dhcpd leases usage analysis

Group: Applications/Communications
License: BSD
URL: https://sourceforge.net/projects/dhcpd-pools
Source: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.xz

BuildRequires: gcc uthash-devel

%description
This is dhcpd-pools - ISC dhcpd lease status utility.

%prep
%autosetup

%build
CFLAGS="%{optflags} -std=c99"
%configure
make %{?_smp_mflags}

%install
#install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}
%make_install

%files
%{_bindir}/%{name}
%{_datarootdir}/*

%changelog
* Fri Mar 25 2022 Ole Ernst <ole.ernst@nmsprime.com> - 3.2-1
- upgpkg

* Fri Mar 25 2022 Ole Ernst <ole.ernst@nmsprime.com> - 3.1-1
- upgpkg

* Tue Mar 17 2020 Ole Ernst <ole.ernst@roetzer-engineering.com> - 3.0-1
- upgpkg

* Fri Aug 25 2017 Ole Ernst <ole.ernst@roetzer-engineering.com> - 2.28-1
- Initial RPM release
