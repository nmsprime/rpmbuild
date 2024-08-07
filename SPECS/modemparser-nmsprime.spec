Name: modemparser-nmsprime
Version: 0.0.4
Release: 1
Summary: A highly efficient modem parser written in Rust

Group: Applications/Communications
License: GPLv3
URL: https://github.com/nmsprime/modemparser

BuildRequires: cargo git openssl-devel rust

%description
A highly efficient modem parser for DOCSIS / SNMP and CWMP / TR069 devices written in Rust.

%prep
git clone git@github.com:nmsprime/modemparser.git
cd modemparser
sed -i "s/vVERSION/v$(git describe --long --tags --abbrev=7 | sed 's/\([^-]*-g\)/r\1/;s/-/./g')/" src/main.rs

%build
cd modemparser
git switch --detach "%{version}"
cargo rustc --release

%install
cd modemparser
install -Dm755 target/release/modemparser %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Thu Jun 27 2024 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.4-1
- Rocky9 release

* Wed Mar 23 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.2-1
- Use PostgreSQL DB now

* Mon Aug 16 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
