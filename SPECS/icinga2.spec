Summary: Network monitoring application

License: GPLv2+

Group: System/Monitoring
Name: icinga2
Version: 2.14.2
Release: 1.el7
Url: https://www.icinga.com/
Source: icinga2-2.14.2.tgz

Requires: icinga2-bin = 2.14.2-1.el7
Requires: icinga2-common = 2.14.2-1.el7

Conflicts: icinga2-common < 2.14.2-1.el7

%description
Meta package for Icinga 2 Core, DB IDO and Web.

%package bin
Summary: Icinga 2 binaries and libraries
Group: System/Monitoring

Requires: icinga2-bin = 2.14.2-1.el7

BuildRequires: libedit-devel
BuildRequires: ncurses-devel

BuildRequires: binutils
BuildRequires: gcc-c++
BuildRequires: libstdc++-devel

BuildRequires: openssl-devel
BuildRequires: bison
BuildRequires: cmake
BuildRequires: flex >= 2.5.35
BuildRequires: make

BuildRequires: boost-devel >= 1.75

BuildRequires: systemd-devel
Requires: systemd

Obsoletes: icinga2-libs <= 2.10.0
Conflicts: icinga2-libs <= 2.10.0

%description bin
Icinga 2 is a general-purpose network monitoring application.
This subpackage provides the binaries for Icinga 2 Core.

%package common
Summary: Common Icinga 2 configuration
Group: System/Monitoring

Requires(pre): shadow-utils
Requires(post): shadow-utils

BuildRequires: logrotate

%description common
This subpackage provides common directories, and the UID and GUID definitions
among Icinga 2 related packages.

%package doc
Summary: Documentation for Icinga 2
Group: Documentation/Other

%description doc
This subpackage provides documentation for Icinga 2.

%package ido-mysql
Summary: IDO MySQL database backend for Icinga 2
Group: System/Monitoring

BuildRequires: mysql-devel

Requires: icinga2-bin = 2.14.2-1.el7

%description ido-mysql
Icinga 2 IDO mysql database backend. Compatible with Icinga 1.x
IDOUtils schema >= 1.12

%package ido-pgsql
Summary: IDO PostgreSQL database backend for Icinga 2
Group: System/Monitoring

BuildRequires: postgresql16-devel

Requires: icinga2-bin = 2.14.2-1.el7

%description ido-pgsql
Icinga 2 IDO PostgreSQL database backend. Compatible with Icinga 1.x
IDOUtils schema >= 1.12

%package selinux
Summary: SELinux policy module supporting icinga2
Group: System/Base
BuildRequires: checkpolicy
BuildRequires: hardlink
BuildRequires: selinux-policy-devel
Requires: icinga2-bin = 2.14.2-1.el7
Requires: icinga-selinux-common

Requires(post): policycoreutils-python
Requires(postun): policycoreutils-python

%description selinux
SELinux policy module supporting icinga2.

%package -n vim-icinga2
Summary: Vim syntax highlighting for icinga2
Group: Productivity/Text/Editors

Requires: vim-filesystem

%description -n vim-icinga2
Provides Vim syntax highlighting for icinga2.

%package -n nano-icinga2
Summary: Nano syntax highlighting for icinga2
Group: Productivity/Text/Editors
Requires: nano

%description -n nano-icinga2
Provides Nano syntax highlighting for icinga2.

%prep
%autosetup
sed -i '1 i\set(Boost_INCLUDE_DIR /usr/include)' CMakeLists.txt
sed -i '1 i\set(PostgreSQL_INCLUDE_DIR /usr/pgsql-13/include)' third-party/cmake/FindPostgreSQL.cmake
sed -i '1 i\set(PostgreSQL_LIBRARY /usr/pgsql-13/lib)' third-party/cmake/FindPostgreSQL.cmake

%build
export CCACHE_BASEDIR="${CCACHE_BASEDIR:-$(pwd)}"

CMAKE_OPTS="-DCMAKE_INSTALL_PREFIX=/usr \
-DCMAKE_INSTALL_SYSCONFDIR=/etc \
-DCMAKE_INSTALL_LOCALSTATEDIR=/var \
-DCMAKE_BUILD_TYPE=RelWithDebInfo \
-DCMAKE_VERBOSE_MAKEFILE=ON \
-DBoost_NO_BOOST_CMAKE=ON \
-DICINGA2_PLUGINDIR=/usr/lib64/nagios/plugins \
-DICINGA2_RUNDIR=/run \
-DICINGA2_SYSCONFIGFILE=/etc/sysconfig/icinga2 \
-DICINGA2_USER=icinga \
-DICINGA2_GROUP=icinga \
-DICINGA2_COMMAND_GROUP=icingacmd"

CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_UNITY_BUILD=ON"

CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_LTO_BUILD=OFF"

CMAKE_OPTS="$CMAKE_OPTS -DINSTALL_SYSTEMD_SERVICE_AND_INITSCRIPT=OFF"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_COMPAT=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_LIVESTATUS=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_NOTIFICATION=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_PERFDATA=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_TESTS=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_MYSQL=ON"
CMAKE_OPTS="$CMAKE_OPTS -DICINGA2_WITH_PGSQL=ON"

CMAKE_OPTS="$CMAKE_OPTS
-DBoost_NO_BOOST_CMAKE=TRUE \
-DBoost_NO_SYSTEM_PATHS=TRUE \
-DBOOST_LIBRARYDIR=/usr/lib64 \
-DBOOST_INCLUDEDIR=/usr/include/boost \
-DBoost_ADDITIONAL_VERSIONS='1.75;1.75.0'"

CMAKE_OPTS="$CMAKE_OPTS -DUSE_SYSTEMD=ON"

cmake3 $CMAKE_OPTS -DCMAKE_C_FLAGS:STRING="-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector-strong --param=ssp-buffer-size=4 -grecord-gcc-switches -m64 -mtune=generic " -DCMAKE_CXX_FLAGS:STRING="-O2 -g -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector-strong --param=ssp-buffer-size=4 -grecord-gcc-switches -m64 -mtune=generic " .

make %_smp_mflags

cd tools/selinux
for selinuxvariant in mls targeted
do
make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
mv icinga2.pp icinga2.pp.${selinuxvariant}
make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install

make install \
DESTDIR="%_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64"

rm -f %_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64//etc/icinga2/features-enabled/*.conf

cd tools/selinux
for selinuxvariant in mls targeted
do
install -d %_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64/usr/share/selinux/${selinuxvariant}
install -p -m 644 icinga2.pp.${selinuxvariant} \
%_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64/usr/share/selinux/${selinuxvariant}/icinga2.pp
done
cd -

install -D -m 0644 tools/syntax/vim/syntax/icinga2.vim %_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64/usr/share/vim/vimfiles/syntax/icinga2.vim
install -D -m 0644 tools/syntax/vim/ftdetect/icinga2.vim %_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64/usr/share/vim/vimfiles/ftdetect/icinga2.vim

install -D -m 0644 tools/syntax/nano/icinga2.nanorc %_topdir/BUILDROOT/icinga2-2.14.2-1.el7.x86_64/usr/share/nano/icinga2.nanorc

%check
export CTEST_OUTPUT_ON_FAILURE=1
make test

%pre

%post

if [ $1 -eq 1 ] ; then
systemctl preset icinga2.service >/dev/null 2>&1 || :
fi

if [ ${1:-0} -eq 1 ]
then
for feature in checker notification mainlog; do
ln -sf ../features-available/${feature}.conf /etc/icinga2/features-enabled/${feature}.conf
done
fi

exit 0

%preun

if [ $1 -eq 0 ] ; then
systemctl --no-reload disable icinga2.service > /dev/null 2>&1 || :
systemctl stop icinga2.service > /dev/null 2>&1 || :
fi

exit 0

%postun

systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
systemctl try-restart icinga2.service >/dev/null 2>&1 || :
fi

if [ "$1" = "0" ]; then
rm -rf /etc/icinga2/features-enabled
fi

exit 0

%pre common
getent group icinga >/dev/null || /usr/sbin/groupadd -r icinga
getent group icingacmd >/dev/null || /usr/sbin/groupadd -r icingacmd
getent passwd icinga >/dev/null || /usr/sbin/useradd -c "icinga" -s /sbin/nologin -r -d /var/spool/icinga2 -G icingacmd -g icinga icinga

%post common

%post ido-mysql
if [ ${1:-0} -eq 1 ] && [ -e /etc/icinga2/features-enabled/ido-mysql.conf ]
then
ln -sf ../features-available/ido-mysql.conf /etc/icinga2/features-enabled/ido-mysql.conf
fi

exit 0

%postun ido-mysql
if [ "$1" = "0" ]; then
rm -f /etc/icinga2/features-enabled/ido-mysql.conf
fi

exit 0

%post ido-pgsql
if [ ${1:-0} -eq 1 ] && [ -e /etc/icinga2/features-enabled/ido-pgsql.conf ]
then
ln -sf ../features-available/ido-pgsql.conf /etc/icinga2/features-enabled/ido-pgsql.conf
fi

exit 0

%postun ido-pgsql
if [ "$1" = "0" ]; then
rm -f /etc/icinga2/features-enabled/ido-pgsql.conf
fi

exit 0

%post selinux
for selinuxvariant in mls targeted
do
/usr/sbin/semodule -s ${selinuxvariant} -i \
/usr/share/selinux/${selinuxvariant}/icinga2.pp &> /dev/null || :
done
/sbin/fixfiles -R icinga2 restore &> /dev/null || :
/sbin/fixfiles -R icinga2-bin restore &> /dev/null || :
/sbin/fixfiles -R icinga2-common restore &> /dev/null || :
/sbin/semanage port -a -t icinga2_port_t -p tcp 5665 &> /dev/null || :

%postun selinux
if [ $1 -eq 0 ] ; then
/sbin/semanage port -d -t icinga2_port_t -p tcp 5665 &> /dev/null || :
for selinuxvariant in mls targeted
do
/usr/sbin/semodule -s ${selinuxvariant} -r icinga2 &> /dev/null || :
done
/sbin/fixfiles -R icinga2 restore &> /dev/null || :
/sbin/fixfiles -R icinga2-bin restore &> /dev/null || :
/sbin/fixfiles -R icinga2-common restore &> /dev/null || :
fi

%files
%defattr(-,root,root,-)
%doc COPYING

%config(noreplace) /etc/logrotate.d/icinga2

%attr(644,root,root) /usr/lib/systemd/system/icinga2.service
%config(noreplace) /etc/sysconfig/icinga2

/usr/sbin/icinga2

%dir /usr/lib//icinga2
/usr/lib//icinga2/prepare-dirs
/usr/lib//icinga2/safe-reload

%attr(0750,icinga,icinga) %dir /etc/icinga2
%attr(0750,icinga,icinga) %dir /etc/icinga2/conf.d
%attr(0750,icinga,icinga) %dir /etc/icinga2/features-available
%exclude /etc/icinga2/features-available/ido-*.conf
%attr(0750,icinga,icinga) %dir /etc/icinga2/features-enabled
%attr(0750,icinga,icinga) %dir /etc/icinga2/scripts
%attr(0750,icinga,icinga) %dir /etc/icinga2/zones.d
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/icinga2.conf
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/constants.conf
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/zones.conf
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/conf.d/*.conf
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/features-available/*.conf
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/zones.d/*
%config(noreplace) /etc/icinga2/scripts/*

%attr(0750,icinga,icingacmd) /var/cache/icinga2
%attr(0750,icinga,icingacmd) %dir /var/log/icinga2
%attr(0750,icinga,icinga) %dir /var/log/icinga2/crash
%attr(0750,icinga,icingacmd) %dir /var/log/icinga2/compat
%attr(0750,icinga,icingacmd) %dir /var/log/icinga2/compat/archives
%attr(0750,icinga,icinga) /var/lib/icinga2
%attr(0750,icinga,icingacmd) %ghost %dir /run/icinga2
%attr(2750,icinga,icingacmd) %ghost /run/icinga2/cmd
%attr(0750,icinga,icinga) %dir /var/spool/icinga2
%attr(0770,icinga,icinga) %dir /var/spool/icinga2/perfdata
%attr(0750,icinga,icinga) %dir /var/spool/icinga2/tmp

%files bin
%defattr(-,root,root,-)
%doc COPYING README.md NEWS AUTHORS CHANGELOG.md
%dir /usr/lib64/icinga2
%dir /usr/lib64/icinga2/sbin
/usr/lib64/icinga2/sbin/icinga2
/usr/lib64/nagios/plugins/check_nscp_api
/usr/share/icinga2
%exclude /usr/share/icinga2/include
/usr/share/man/man8/icinga2.8.gz

%files common
%defattr(-,root,root,-)
%doc COPYING README.md NEWS AUTHORS CHANGELOG.md tools/syntax
/etc/bash_completion.d/icinga2
%attr(0750,icinga,icinga) %dir /usr/share/icinga2/include
/usr/share/icinga2/include/*

%files doc
%defattr(-,root,root,-)
/usr/share/doc/icinga2
%docdir /usr/share/doc/icinga2

%files ido-mysql
%defattr(-,root,root,-)
%doc COPYING README.md NEWS AUTHORS CHANGELOG.md
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/features-available/ido-mysql.conf
/usr/lib64/icinga2/libmysql_shim*
/usr/share/icinga2-ido-mysql

%files ido-pgsql
%defattr(-,root,root,-)
%doc COPYING README.md NEWS AUTHORS CHANGELOG.md
%config(noreplace) %attr(0640,icinga,icinga) /etc/icinga2/features-available/ido-pgsql.conf
/usr/lib64/icinga2/libpgsql_shim*
/usr/share/icinga2-ido-pgsql

%files selinux
%defattr(-,root,root,0755)
%doc tools/selinux/*
/usr/share/selinux/*/icinga2.pp

%files -n vim-icinga2
%defattr(-,root,root,-)
/usr/share/vim/vimfiles/syntax/icinga2.vim
/usr/share/vim/vimfiles/ftdetect/icinga2.vim

%files -n nano-icinga2
%defattr(-,root,root,-)
/usr/share/nano/icinga2.nanorc

%changelog
* Thu Jan 18 2024 Icinga GmbH <info@icinga.com> - 2.14.2-1.el7
- Version 2.14.2-1

