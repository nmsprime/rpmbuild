Name: icingaweb2-module-incubator
Version: 0.6.0
Release: 2
Summary: Bleeding edge Icinga Web 2 libraries

Group: Applications/Communications
License: MIT
URL: https://github.com/Icinga/%{name}
Source: https://github.com/Icinga/%{name}/archive/refs/tags/v%{version}.tar.gz

Requires: icinga2 icingacli

%description
This repository ships bleeding edge libraries useful for Icinga Web 2 modules. Please download the latest release and install it like any other module.

%prep
%autosetup

%install
install -dm755 %{buildroot}%{_datarootdir}/icingaweb2/modules/incubator
mv * %{buildroot}%{_datarootdir}/icingaweb2/modules/incubator/

%post
icingacli module enable incubator
systemctl restart icinga2.service

%files
%{_datarootdir}/icingaweb2/modules/incubator/*

%changelog
* Fri Jan 07 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 0.6.0-2
- Add dependencies

* Thu Oct 07 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.6.0-1
- Initial RPM release
