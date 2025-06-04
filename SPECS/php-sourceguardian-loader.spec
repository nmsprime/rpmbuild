%global debug_package %{nil}

Name: php-sourceguardian-loader
Version: 15.0.0
Release: 1
Summary: The SourceGuardian Loader

Group: Applications/Communications
License: proprietary
URL: https://www.sourceguardian.com
Source: https://www.sourceguardian.com/loaders/download/loaders.linux-x86_64.tar.bz2

%description
Using SourceGuardian encoded and secured PHP files requires a file called the
SourceGuardian loader to be installed on the server and made available to PHP.

%prep
%autosetup -c %{name}-%{version}

%build
mv "SourceGuardian Loader License.pdf" LICENSE.pdf
cat << EOF > 01-sourceguardian_loader.ini
; Enable sourceguardian_loader extension module
zend_extension = ixed.8.3.lin
EOF

%install
install -Dm644 01-sourceguardian_loader.ini %{buildroot}%{_sysconfdir}/php.d/01-sourceguardian_loader.ini
install -Dm755 ixed.8.3.lin %{buildroot}/usr/lib64/php/modules/ixed.8.3.lin

%files
%doc README
%license LICENSE.pdf
%config(noreplace) %{_sysconfdir}/php.d/01-sourceguardian_loader.ini
/usr/lib64/php/modules/ixed.8.3.lin

%changelog
* Wed May 08 2024 Ole Ernst <ole.ernst@nmsprime.com> - 15.0.0-1
- Upgrade php-sourceguardian-loader for PHP8.3

* Fri Nov 11 2022 Ole Ernst <ole.ernst@nmsprime.com> - 12.1.1-3
- Use native php version for Almalinux 9

* Thu Jan 06 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 12.1.1-2
- Fix: Restart PHP8 after changing ini

* Wed Dec 01 2021 Ole Ernst <ole.ernst@nmsprime.com> - 12.1.1-1
- Initial RPM release
