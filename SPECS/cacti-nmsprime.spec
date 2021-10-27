%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}
%define name_org cacti

Name: cacti-nmsprime
Version: 1.2.18
Release: 1%{?dist}
Summary: An rrd based graphing tool
License: GPLv2+
URL: https://www.cacti.net/
Source0: https://www.cacti.net/downloads/%{name_org}-%{version}.tar.gz
Source1: cacti-httpd.conf
Source2: cacti.logrotate
Source3: %{name_org}.cron
Patch0: cacti-1.2.x-disable_log_rotation.patch
Patch1: cacti-1.2.x-csrf-secret.patch

BuildArch: noarch

# Requires PHP 5.4+
Requires: php(language) >= 5.4

# DB access is managed via pdo_mysql
Requires: php-pdo_mysql

# Core PHP libs/extensions required by Cacti
Requires: php-pdo
Requires: php-reflection
Requires: php-simplexml
Requires: php-ctype
Requires: php-date
Requires: php-dom
Requires: php-gettext
Requires: php-filter
Requires: php-gd
Requires: php-gmp
Requires: php-hash
Requires: php-iconv
Requires: php-intl
Requires: php-json
Requires: php-ldap
Requires: php-mbstring
Requires: php-openssl
Requires: php-pcntl
Requires: php-pcre
Requires: php-posix
Requires: php-session
Requires: php-snmp
Requires: php-sockets
Requires: php-spl
Requires: php-xml
Requires: php-zlib

# Cacti Requirements
Requires: mysql
Requires: httpd
Requires: rrdtool
Requires: net-snmp
Requires: net-snmp-utils
Requires: crontabs

# Bundled JS library
Provides: bundled(js-jquery) = 3.4.1
Provides: bundled(js-storage) = 1.0.4
Provides: bundled(js-tree) = 3.3.8

%description
Cacti is a complete frontend to RRDTool. It stores all of the
necessary information to create graphs and populate them with
data in a MySQL database. The frontend is completely PHP
driven.

%prep
%autosetup -p1 -n %{name_org}-%{version}

%build
# Nothing to build

%install
%{__mkdir} -p %{buildroot}/%{_sysconfdir}/%{name_org}
%{__install} -d -m 0755 %{buildroot}/%{_pkgdocdir}
%{__install} -d -m 0755 %{buildroot}/%{_datadir}/%{name_org}/
%{__install} -d -m 0755 cache/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/cache
%{__install} -d -m 0755 cli/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/cli
%{__install} -d -m 0775 log/ %{buildroot}/%{_localstatedir}/log/%{name_org}/
%{__install} -d -m 0755 resource/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/resource
%{__install} -d -m 0755 rra/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/rra/
%{__install} -d -m 0755 scripts/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/scripts/
%{__install} -d -m 0755 csrf/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/csrf/
%{__mv} *.php %{buildroot}/%{_datadir}/%{name_org}/
%{__mv} cache/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/
%{__mv} cli/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/
%{__mv} resource/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/
%{__mv} rra/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/
%{__mv} scripts/ %{buildroot}/%{_localstatedir}/lib/%{name_org}/
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/cron.d/%{name_org}
%{__install} -D -m 0644 %{SOURCE1} %{buildroot}/%{_sysconfdir}/httpd/conf.d/%{name_org}.conf
%{__install} -D -m 0644 %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/cacti
%{__cp} -ar formats/ images/ include/ install/ lib/ locales/ mibs/ plugins/ %{buildroot}%{_datadir}/%{name_org}
%{__cp} -a docs/ %{buildroot}/%{_pkgdocdir}
%{__mv} %{buildroot}/%{_datadir}/%{name_org}/include/config.php %{buildroot}/%{_sysconfdir}/%{name_org}/db.php
%{__chmod} +x %{buildroot}/%{_datadir}/%{name_org}/cmd.php %{buildroot}/%{_datadir}/%{name_org}/poller.php
ln -s %{_localstatedir}/lib/%{name_org}/cache %{buildroot}/%{_datadir}/%{name_org}/
ln -s %{_localstatedir}/lib/%{name_org}/cli %{buildroot}/%{_datadir}/%{name_org}/
ln -s %{_sysconfdir}/%{name_org}/db.php %{buildroot}/%{_datadir}/%{name_org}/include/config.php
ln -s %{_localstatedir}/lib/%{name_org}/resource %{buildroot}/%{_datadir}/%{name_org}/
ln -s %{_localstatedir}/lib/%{name_org}/rra %{buildroot}/%{_datadir}/%{name_org}/
ln -s %{_localstatedir}/lib/%{name_org}/scripts %{buildroot}/%{_datadir}/%{name_org}/
ln -s %{_localstatedir}/log/%{name_org}/ %{buildroot}/%{_datadir}/%{name_org}/log
ln -s %{_datadir}/%{name_org}/lib %{buildroot}/%{_localstatedir}/lib/%{name_org}/
ln -s %{_datadir}/%{name_org}/include %{buildroot}/%{_localstatedir}/lib/%{name_org}/
# Create logfiles
touch %{buildroot}/%{_localstatedir}/log/%{name_org}/%{name_org}.log
touch %{buildroot}/%{_localstatedir}/log/%{name_org}/%{name_org}_stderr.log
# Create csrf-secret.php
touch %{buildroot}/%{_localstatedir}/lib/%{name_org}/csrf/csrf-secret.php

# Migrate /usr/share/cacti/resource to /var/cacti/resource
%pretrans -p <lua>
path = "/usr/share/cacti/resource"
st = posix.stat(path)
if st and st.type == "directory" then
  status = os.rename(path, path .. ".rpmmoved")
  if not status then
    suffix = 0
    while not status do
      suffix = suffix + 1
      status = os.rename(path .. ".rpmmoved", path .. ".rpmmoved." .. suffix)
    end
    os.rename(path, path .. ".rpmmoved")
  end
end

%post
# Migrate file ownership to apache user
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/cache/
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/cli/
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/csrf/
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/resource/
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/rra/
chown -R apache:apache %{_localstatedir}/lib/%{name_org}/scripts/
chown -R apache:apache %{_localstatedir}/log/%{name_org}/
chown root:apache %{_sysconfdir}/%{name_org}/db.php

# SELinux
semanage fcontext -a -t httpd_sys_content_t '%{_sysconfdir}/%{name_org}/db.php' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/cache(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/cli(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/csrf(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/resource(/.*)?' 2>/dev/null || :
semanage fcontext -a -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/scripts(/.*)?' 2>/dev/null || :
restorecon -R %{_localstatedir}/lib/%{name_org} || :
restorecon -R %{_sysconfdir}/%{name_org} || :

# Migrate cacti polller to apache user

sed -i -e 's/\tcacti\t/\tapache\t/' %{_sysconfdir}/cron.d/%{name_org}

%postun
if [ $1 -eq 0  ] ; then
semanage fcontext -d -t httpd_sys_content_t '%{_sysconfdir}/%{name_org}/db.php' 2>/dev/null || :
semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/cache(/.*)?' 2>/dev/null || :
semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/cli(/.*)?' 2>/dev/null || :
semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/csrf(/.*)?' 2>/dev/null || :
semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/resource(/.*)?' 2>/dev/null || :
semanage fcontext -d -t httpd_sys_rw_content_t '%{_localstatedir}/lib/%{name_org}/scripts(/.*)?' 2>/dev/null || :
fi

%files
%doc docs/ README.md cacti.sql
%license LICENSE
%dir %{_sysconfdir}/%{name_org}
%dir %{_datadir}/%{name_org}
%dir %{_localstatedir}/lib/%{name_org}
%dir %{_localstatedir}/lib/%{name_org}/cli
%dir %attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/csrf
%dir %attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/scripts
%dir %attr(-,apache,apache) %{_localstatedir}/log/%{name_org}/
%config(noreplace) %attr(-,apache,apache) %{_localstatedir}/log/%{name_org}/%{name_org}.log
%config(noreplace) %attr(-,apache,apache) %{_localstatedir}/log/%{name_org}/%{name_org}_stderr.log
%config(noreplace) %{_sysconfdir}/cron.d/cacti
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name_org}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name_org}
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/%{name_org}/db.php
%{_datadir}/%{name_org}/*.php
%{_datadir}/%{name_org}/cache
%{_datadir}/%{name_org}/cli
%{_datadir}/%{name_org}/formats/
%{_datadir}/%{name_org}/images/
%{_datadir}/%{name_org}/include/
%{_datadir}/%{name_org}/install/
%{_datadir}/%{name_org}/lib/
%{_datadir}/%{name_org}/locales/*
%{_datadir}/%{name_org}/log
%{_datadir}/%{name_org}/mibs
%{_datadir}/%{name_org}/plugins/
%{_datadir}/%{name_org}/resource
%{_datadir}/%{name_org}/rra
%{_datadir}/%{name_org}/scripts
%{_localstatedir}/lib/%{name_org}/scripts/*[^p]
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/scripts/*.php
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/resource/
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/rra/
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/cache/
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/cli/*php
%attr(-,apache,apache) %{_localstatedir}/lib/%{name_org}/cli/.htaccess
%attr(0770,apache,apache) %{_localstatedir}/lib/%{name_org}/csrf/csrf-secret.php
%attr(-,root,root) %{_localstatedir}/lib/%{name_org}/include
%attr(-,root,root) %{_localstatedir}/lib/%{name_org}/lib
%ghost %{_datadir}/%{name_org}/resource.rpmmoved

%changelog
* Wed Oct 27 2021 Ole Ernst <ole.ernst@nmsprime.com> - 1.2.18-1
- Update to 1.2.18

* Tue Nov 03 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.15-1
- Update to 1.2.15

* Thu Aug 06 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.14-1
- Update to 1.2.14

* Tue Jul 14 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.13-1
- Update to 1.2.13
- CVE-2020-11022, CVE-2020-11023, CVE-2020-13625, CVE-2020-14295

* Wed May 27 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.12-1
- Update to 1.2.12

* Tue Apr 07 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.11-1
- Update to 1.2.11

* Mon Mar 02 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.10-1
- Update to 1.2.10
- CVE-2020-8813

* Mon Feb 10 2020 Morten Stevens <mstevens@fedoraproject.org> - 1.2.9-1
- Update to 1.2.9
- CVE-2020-7106, CVE-2020-7237

* Wed Dec 11 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.8-1
- Update to 1.2.8
- CVE-2019-17357, CVE-2019-17358, CVE-2019-16723

* Sat Nov 30 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.7-1
- Update to 1.2.7

* Tue Sep 03 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.6-1
- Update to 1.2.6
- Don't require php-imap

* Sat Jul 20 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.5-1
- Update to 1.2.5

* Sat Jun 08 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.4-1
- Update to 1.2.4

* Sun Mar 31 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.3-1
- Update to 1.2.3

* Mon Feb 25 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.2-1
- Update to 1.2.2
- SELinux improvements
- Packaging improvements

* Thu Jan 17 2019 Morten Stevens <mstevens@fedoraproject.org> - 1.2.0-1
- Rebase to 1.2.0
- Multiple cross-site scripting vulnerabilities fixed in 1.2.0
- CVE-2018-20723, CVE-2018-20724, CVE-2018-20725, CVE-2018-20726 (#1667024)

* Mon Dec 03 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.38-4
- Spec file improvements
- Updated logrotation settings
- Removed cacti user
- Changed rra file ownership to apache #1454755

* Wed Jul 25 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.38-2
- Fix for https://github.com/Cacti/cacti/issues/1634

* Wed May 16 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.38-1
- Update to 1.1.38

* Mon Mar 26 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.37-1
- Update to 1.1.37

* Mon Feb 26 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.36-1
- Update to 1.1.36

* Tue Feb 13 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.35-1
- Update to 1.1.35

* Tue Feb 06 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.34-1
- Update to 1.1.34

* Wed Jan 24 2018 Morten Stevens <mstevens@fedoraproject.org> - 1.1.33-1
- Update to 1.1.33

* Sun Nov 19 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.28-1
- Update to 1.1.28
- CVE-2017-16641, CVE-2017-16660, CVE-2017-16661, CVE-2017-16785

* Mon Oct 23 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.27-1
- Update to 1.1.27

* Tue Oct 17 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.26-1
- Update to 1.1.26
- CVE-2017-15194

* Mon Sep 18 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.24-1
- Update to 1.1.24

* Tue Sep 05 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.21-1
- Update to 1.1.21

* Mon Aug 21 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.19-1
- Update to 1.1.19

* Sun Aug 13 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.17-1
- Update to 1.1.17

* Sun Jul 30 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.16-1
- Update to 1.1.16

* Tue Jul 25 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.15-1
- Update to 1.1.15

* Mon Jul 24 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.14-1
- Update to 1.1.14

* Fri Jul 14 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.13-1
- Update to 1.1.13

* Thu Jul 06 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.12-2
- Fix Cross-site Scripting (XSS) issue with link.php

* Wed Jul 05 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.12-1
- Update to 1.1.12

* Tue Jul 04 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.11-1
- Update to 1.1.11

* Mon Jun 12 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.10-1
- Update to 1.1.10

* Mon May 22 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.7-1
- Update to 1.1.7

* Sat May 13 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.6-2
- Fix PHP requirements
- Cacti db access not compatible with PHP 7 (#1450578)

* Mon May 08 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.6-1
- Update to 1.1.6

* Wed Apr 26 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.5-1
- Update to 1.1.5

* Mon Apr 24 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.4-1
- Update to 1.1.4

* Sun Apr 16 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.3-1
- Update to 1.1.3

* Wed Apr 12 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.2-2
- Work with several MySQL variants (#1440755)

* Mon Apr 03 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.2-1
- Update to 1.1.2

* Tue Mar 28 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.1-1
- Update to 1.1.1

* Mon Mar 20 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.1.0-1
- Update to 1.1.0

* Wed Mar 15 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.6-1
- Update to 1.0.6

* Mon Mar 13 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.5-1
- Update to 1.0.5
- Logfile improvements
- Added php-gd and php-process as dependency (#1430893)

* Mon Feb 27 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.4-1
- Update to 1.0.4

* Sat Feb 18 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.3-2
- Cacti 1.0.x spec file improvements

* Thu Feb 16 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.3-1
- Update to 1.0.3

* Sun Feb 12 2017 Morten Stevens <mstevens@fedoraproject.org> - 1.0.2-1
- Update to 1.0.2

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.8.8h-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Jan 18 2017 Morten Stevens <mstevens@fedoraproject.org> - 0.8.8h-3
- Fixes for PHP7 backported from Arch Linux (#1390770)

* Tue Jun 28 2016 Jon Ciesla <limburgher@gmail.com> - 0.8.8h-2
- php7 Requires fix.

* Mon May 09 2016 Morten Stevens <mstevens@fedoraproject.org> - 0.8.8h-1
- Update to 0.8.8h
- CVE-2016-3659

* Fri Apr 15 2016 Morten Stevens <mstevens@fedoraproject.org> - 0.8.8g-1
- Update to 0.8.8g
- Improve spec file (#1302904)

* Fri Jan 29 2016 Morten Stevens <mstevens@fedoraproject.org> - 0.8.8f-2
- CVE-2015-8369: SQL Injection vulnerability in graph.php
- CVE-2015-8377: Fix SQL Injection vulnerability in graphs_new.php
- CVE-2015-8604: Fix SQL Injection vulnerability in graphs_new.php

* Fri Jan 29 2016 Morten Stevens <mstevens@fedoraproject.org> - 0.8.8f-1
- Update to 0.8.8f

* Fri Jun 27 2014 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-7
- Patches for CVE-2014-4002 Cross-site scripting vulnerability
  (RHBZ #1113035)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.8b-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Apr 07 2014 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-5
- Patch for CVE-2014-2708 SQL injection issues in graph_xport.php
  (RHBZ #1084258)
- Patch for CVE-2014-2709 shell escaping issues in lib/rrd.php
  (RHBZ #1084258)
- Patch for CVE-2014-2326 stored XSS attack (RHBZ #1082122)
- Patch for CVE-2014-2328 use of exec-like function calls without safety
  checks allow arbitrary command execution (RHBZ #1082122)

* Fri Feb 07 2014 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-4
- Move cron to a separate file and require crontabs (RHBZ #947047). Thanks
  Jóhann B. Guðmundsson.
- Update for systemd (RHBZ #947047). Thanks Jóhann B. Guðmundsson.
- Fix rpmlint warning about spaces-to-tabs

* Wed Sep 04 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-3
- Fix comments in thumbnails (BZ #1004550)

* Mon Aug 26 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-2
- Patch for CVE-2013-5588 and CVE-2013-5589 (BZ #1000860)

* Wed Aug 07 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8b-1
- New upstream release (BZ #993042)

* Mon Jul 29 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-9
- Use %%{_pkgdocdir}, per
  https://fedoraproject.org/wiki/Changes/UnversionedDocdirs

* Sun Jul 14 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-8
- Improve security description in cacti's httpd conf (RHBZ #895823)
- Use improved treeview replacement patch (RHBZ #888207)
- rpmlint fixes
- trim RPM changelog

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.8a-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 08 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-6
- Add note to README.fedora about the default MySQL password
- Remove reference to "docs/INSTALL" in README.fedora (RHBZ #893122)
- Add dependency on net-snmp-utils (RHBZ #893150)

* Fri Jan 04 2013 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-5
- Install our README file as README.fedora

* Fri Jan  4 2013 Tom Callaway <spot@fedoraproject.org> - 0.8.8a-4
- remove non-free treeview bits (replace with jquery future code from 0.8.9 trunk)

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.8a-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Thu Jun 28 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-2
- Add plugins directory (BZ #834355)
- Drop Fedora 15 (EOL) from logrotate syntax adjustment

* Mon Apr 30 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8a-1
- New upstream release (BZ #817506)
- Drop upstreamed $url_path patch

* Wed Apr 11 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8-3
- Patch $url_path to default to "/cacti/" (upstream bug 2217)

* Fri Apr 06 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8-2
- Adjust httpd ACL conditionals to test the presence of mod_authz_core
  (as discussed on fedora-devel)

* Wed Apr 04 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.8-1
- New upstream release (BZ #809753).

* Mon Mar 26 2012 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.7i-4
- Adjust ACLs to support httpd 2.4.

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.7i-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Dec 13 2011 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.7i-2
- Only set "su" logrotate parameter for F16 and above.
- Tweak mod_security rules.

* Mon Dec 12 2011 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.7i-1
- New upstream release (BZ #766573).

* Fri Nov 11 2011 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.7h-2
- block HTTP access to log and rra directories (#609856)
- overrides for mod_security
- set logrotate to su to cacti apache when rotating (#753079)

* Thu Oct 27 2011 Ken Dreyer <ktdreyer@ktdreyer.com> - 0.8.7h-1
- New upstream release.
- Remove upstream'd mysql patch.

* Mon Aug 08 2011 Jon Ciesla <limb@jcomserv.net> - 0.8.7g-3
- Patch for MySQL 5.5, BZ 728513.

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.7g-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jul 12 2010 Mike McGrath <mmcgrath@redhat.com> 0.8.7g-1
- Upstream released new version

* Mon May 24 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7f-1
- Upstream released new version
- Contains security updates #595289

* Fri Apr 23 2010 Mike McGrath <mmcgrath@redhat.com> - 0.8.7e-4
- Pulling in patches from upstream
- SQL injection fix
- BZ #541279

* Tue Dec  1 2009 Mike McGrath <mmcgrath@redhat.com> - 0.8.7e-3
- Pulling in some official patches
- #541279
- #541962

* Sun Aug 16 2009 Mike McGrath <mmcgrath@redhat.com> - 0.8.7e-1
- Upstream released new version

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.7d-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Mar 31 2009 Michael Schwendt <mschwendt@fedoraproject.org> - 0.8.7d-3
- Fix unowned cli directory (#473631)

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.8.7d-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sat Feb 21 2009 Mike McGrath <mmcgrath@redhat.com> - 0.8.7d-1
- Upstream released new version

* Mon Jul 28 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.7b-4
- Added cli directory

* Fri Jul 18 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0.8.7b-3
- fix my own mistake in the license tag

* Tue Jul 15 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 0.8.7b-2
- fix license tag

* Thu Feb 14 2008 Mike McGrath <mmcgrath@redhat.com> - 0.8.7b-1
- Upstream released new version

* Fri Nov 23 2007 Mike McGrath <mmcgrath@redhat.com> - 0.8.7a-2
- db.php is now 640 instead of 660 - #396331

* Tue Nov 20 2007 Mike McGrath <mmcgrath@redhat.com> - 0.8.7a-1
- Upstream released new version
- Fixes for bug #391691 - CVE-2007-6035
