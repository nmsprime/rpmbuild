%global debug_package %{nil}

Name: obudpst
Version: 7.4.0
Release: 1
Summary: OB-UDPST is a client/server utility to do UDP-based IP capacity measurements

Group: Applications/Communications
License: BSD
URL: https://github.com/BroadbandForum/%{name}
Source: https://github.com/BroadbandForum/%{name}/archive/refs/tags/v%{version}.tar.gz
BuildRequires: cmake make openssl-devel

%description
OB-UDPST is a client/server utility to do UDP-based IP capacity measurements (see TR-471 for details).

%prep
%autosetup

%build
cat << EOF > udpst.service
[Unit]
Description=OB-UDPST
After=network.target

[Service]
User=nobody
ExecStart=/usr/bin/udpst
Restart=always

[Install]
WantedBy=default.target
EOF

cmake .
make %{?_smp_mflags}

%install
install -Dm755 udpst %{buildroot}%{_bindir}/udpst
install -Dm 644 udpst.service %{buildroot}%{_unitdir}/udpst.service

%files
%{_bindir}/udpst
%{_unitdir}/udpst.service

%changelog
* Mon Jun 08 2026 Ole Ernst <ole.ernst@nmsprime.com> - 7.4.0-1
- Initial RPM release
