Name: voipmonitor
Version: 2024.08.1
Release: 1
Summary: A live network packet sniffer which analyze SIP and RTP protocol

Group: Applications/Communications
License: GPLv2
URL: https://www.%{name}.org
Source0: https://sourceforge.net/projects/%{name}/files/2024.08/%{name}-amd64-%{version}-static.tar.gz
Source1: https://raw.githubusercontent.com/%{name}/sniffer/c899707257d547351b068bcdede55af343af9c0e/config/systemd/%{name}.service

Requires: curl, json-c, mariadb-server, rrdtool, snappy, unixODBC

%description
VoIPmonitor is open source live network packet sniffer which analyze SIP
and RTP protocol. It can run as daemon or analyzes already captured pcap
files. For each detected VoIP call voipmonitor calculates statistics about
loss, burstiness, latency and predicts MOS (Meaning Opinion Score) according
to ITU-T G.107 E-model. These statistics are saved to MySQL database and each
call is saved as pcap dump. Web PHP application (it is not part of open
source sniffer) filters data from database and graphs latency and loss
distribution. Voipmonitor also detects improperly terminated calls when
BYE or OK was not seen. To accuratly transform latency to loss packets,
voipmonitor simulates fixed and adaptive jitterbuffer.

%prep
%autosetup -n %{name}-amd64-%{version}-static

%install
install -Dm755 usr/local/sbin/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm644 etc/%{name}.conf %{buildroot}%{_sysconfdir}/%{name}.conf
install -Dm644 %{_sourcedir}/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -d %{buildroot}%{_localstatedir}/spool/%{name}

%files
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}.conf
%dir %{_localstatedir}/spool/%{name}

%changelog
* Wed Aug 07 2024 Ole Ernst <ole.ernst@nmsprime.com> - 2024.08.1-1
- Update 2024.08.01

* Thu Jan 04 2024 Ole Ernst <ole.ernst@roetzer-engineering.com> - 2024.01-1
- Update 2024.01

* Mon Jun 13 2016 Ole Ernst <ole.ernst@roetzer-engineering.com> - 16.0.2-1
- Initial RPM release
