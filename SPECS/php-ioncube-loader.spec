Name: php-ioncube-loader
Version: 10.4.5
Release: 1
Summary: The ionCube Loader

Group: Applications/Communications
License: proprietary
URL: https://ioncube.com
Source: https://downloads.ioncube.com/loader_downloads/ioncube_loaders_lin_x86-64.tar.gz

%description
Using ionCube encoded and secured PHP files requires a file called the ionCube
Loader to be installed on the web server and made available to PHP.

%prep
%autosetup -n ioncube

%build
cat << EOF > 01-ioncube_loader.ini
; Enable ioncube_loader extension module
zend_extension = ioncube_loader.so
EOF

%install
install -Dm644 01-ioncube_loader.ini %{buildroot}%{_sysconfdir}/php.d/01-ioncube_loader.ini
install -Dm644 01-ioncube_loader.ini %{buildroot}%{_sysconfdir}/opt/rh/rh-php73/php.d/01-ioncube_loader.ini
install -Dm755 ioncube_loader_lin_7.3.so %{buildroot}%{_libdir}/php/modules/ioncube_loader.so
install -Dm755 ioncube_loader_lin_7.3.so %{buildroot}/opt/rh/rh-php73/root/usr/lib64/php/modules/ioncube_loader.so

%files
%doc USER-GUIDE.txt
%license LICENSE.txt
%config(noreplace) %{_sysconfdir}/php.d/01-ioncube_loader.ini
%config(noreplace) %{_sysconfdir}/opt/rh/rh-php73/php.d/01-ioncube_loader.ini
%{_libdir}/php/modules/ioncube_loader.so
/opt/rh/rh-php73/root/usr/lib64/php/modules/ioncube_loader.so

%changelog
* Tue Apr 06 2021 Ole Ernst <ole.ernst@nmsprime.com> - 10.4.5-1
- Initial RPM release
