Name: modemparser-nmsprime
Version: 0.0.1
Release: 1
Summary: A highly efficient modem parser written in Rust

Group: Applications/Communications
License: GPLv3
URL: https://github.com/nmsprime/modemparser
Source: https://github.com/nmsprime/modemparser/archive/refs/heads/main.tar.gz

BuildRequires: cargo openssl-devel rust

%description
A highly efficient modem parser for DOCSIS / SNMP and CWMP / TR069 devices written in Rust.

%prep
%autosetup -p1 -n modemparser-main

%build
cargo rustc --release

%install
install -Dm755 target/release/modemparser %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Mon Aug 16 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
