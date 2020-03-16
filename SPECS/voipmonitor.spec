Name: voipmonitor
Version: 16.0.2
Release: 1
Summary: A live network packet sniffer which analyze SIP and RTP protocol

Group: Applications/Communications
License: GPLv2
URL: https://www.voipmonitor.org
Source: https://github.com/%{name}/sniffer/archive/b47e0d2.tar.gz

BuildRequires: curl-devel, json-c-devel, fftw-devel, gnutls-devel, libogg-devel
BuildRequires: libpcap-devel, libgcrypt-devel, libpng-devel, libssh-devel
BuildRequires: libxml2-devel, libvorbis-devel, lzo-devel, mariadb-devel
BuildRequires: rrdtool-devel, snappy-devel, unixODBC-devel, zlib-devel
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
%autosetup -n sniffer-b47e0d2cd9af01ec029601a4b6dd13d76edd7b91

%build
autoreconf -vfi
%configure
make %{?_smp_mflags}

%install
install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}
install -Dm644 config/%{name}.conf %{buildroot}%{_sysconfdir}/%{name}.conf
install -Dm644 config/systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
install -d %{buildroot}%{_localstatedir}/spool/%{name}

%files
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}.conf
%dir %{_localstatedir}/spool/%{name}

%changelog
* Mon Jun 13 2016 Ole Ernst <ole.ernst@roetzer-engineering.com> - 16.0.2-1
- Initial RPM release
