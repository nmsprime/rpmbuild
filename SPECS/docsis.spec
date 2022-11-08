Name: docsis
Version: 0.9.8.r393.gd7c9643
Release: 2
Summary: Human-readable text to binary configuration file converter

Group: Applications/Communications
License: GPLv2
URL: http://docsis.sourceforge.net
Source: https://github.com/rlaager/%{name}/archive/d7c9643.tar.gz
Patch: docsis_dialplan.patch

BuildRequires: autoconf automake libtool glib2-devel bison flex net-snmp-devel

%description
This program encodes a DOCSIS binary configuration file from a human-readable
text configuration file. This tool is fully compliant with the following specs:
CM-SP-eRouter-I12, DPoE-SP-DEMARCv1.0-I04, CM-SP-L2VPN-I13, CM-SP-MULPIv3.0-I24

%prep
%autosetup -p1 -n docsis-d7c9643a66bff27278cf9096e7e4a6b7c0427142
sed -i 's/\[gm4 gnum4 m4\], \[notfound\],\[/\[gm4 gnum4 m4\], \[notfound\],\[\/usr\/bin:/' configure.ac

%build
./autogen.sh
%configure
make %{?_smp_mflags}
rm mibs/Makefile*
find mibs -maxdepth 1 -type f ! -name 'Makefile*' -exec mv '{}' '{}'.txt \;

%install
install -Dm755 src/%{name} %{buildroot}%{_bindir}/%{name}
install -d %{buildroot}%{_datarootdir}/snmp/mibs
cp mibs/*.txt %{buildroot}%{_datarootdir}/snmp/mibs

%files
%{_bindir}/%{name}
%{_datarootdir}/snmp/mibs/*.txt

%changelog
* Tue Nov 08 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.9.8.r393.gd7c9643-2
- Fix compiling with Almalinux 9

* Wed May 05 2021 Ole Ernst <ole.ernst@nmsprime.com> - 0.9.8.r393.gd7c9643-1
- Add dialplan from user-supplied file and add IETF MTA hash

* Mon Jun 12 2017 Ole Ernst <ole.ernst@roetzer-engineering.com> - 0.9.8.r391.g6b23fd2-1
- Initial RPM release
