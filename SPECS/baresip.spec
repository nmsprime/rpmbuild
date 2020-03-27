%define name     baresip
%define ver      0.6.5
%define rel      1

Summary: Portable and modular SIP User-Agent with audio and video support.
Name: %name
Version: %ver
Release: %rel
License: BSD
Group: Applications/Devel
Source0: file://%{name}-%{version}.tar.gz
URL: http://www.creytiv.com/
Vendor: Creytiv
Packager: Ole Ernst <ole.ernst@nmsprime.com>
BuildRoot: /var/tmp/%{name}-build-root
Requires: re rem
BuildRequires: re-devel rem-devel

%description
Portable and modular SIP User-Agent with audio and video support.

%prep
%setup

%build
make PREFIX=/usr RELEASE=1

cat << EOF > %{name}.service
[Unit]
Description=%{name}
After=network.target

[Service]
User=apache
ExecStart=%{_bindir}/%{name} -f /var/www/nmsprime/storage/app/config/%{name}
Restart=always

[Install]
WantedBy=default.target
EOF

%install
rm -rf $RPM_BUILD_ROOT
make PREFIX=/usr DESTDIR=$RPM_BUILD_ROOT install \
%ifarch x86_64
	LIBDIR=/usr/lib64
%endif
install -D -m 644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service

%clean
rm -rf $RPM_BUILD_ROOT

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%{_datadir}/baresip/*.png
%{_datadir}/baresip/*.wav
%{_unitdir}/%{name}.service
%{_libdir}/%{name}/modules/*.so*
%attr(755,root,root) %{_bindir}/%{name}

%changelog
* Thu Mar 26 2020 Ole Ernst <ole.ernst@nmsprime.com> - 0.6.5-1
- Initial RPM release
