Name: php-sourceguardian-loader
Version: 12.1.3
Release: 1
Summary: The SourceGuardian Loader
Conflicts: php-ioncube-loader
Obsoletes: php-ioncube-loader <= 10.4.5

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
zend_extension = ixed.8.0.lin
EOF

%install
install -Dm644 01-sourceguardian_loader.ini %{buildroot}%{_sysconfdir}/opt/remi/php80/php.d/01-sourceguardian_loader.ini
install -Dm755 ixed.8.0.lin %{buildroot}/opt/remi/php80/root/usr/lib64/php/modules/ixed.8.0.lin

systemctl restart php80-php-fpm.service

%files
%doc README
%license LICENSE.pdf
%config(noreplace) %{_sysconfdir}/opt/remi/php80/php.d/01-sourceguardian_loader.ini
/opt/remi/php80/root/usr/lib64/php/modules/ixed.8.0.lin

%changelog
* Thu Jan 06 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 12.1.3-1
- Fix: Restart PHP8 after changing ini

* Wed Dec 01 2021 Ole Ernst <ole.ernst@nmsprime.com> - 12.1.2-1
- Initial RPM release
