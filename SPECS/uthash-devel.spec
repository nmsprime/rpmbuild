Name: uthash-devel
Version: 2.3.0
Release: 1
Summary: C preprocessor implementations of a hash table and a linked list

Group: Applications/Communications
License: BSD
BuildArch: noarch
URL: https://troydhanson.github.io/uthash
Source: https://github.com/troydhanson/uthash/archive/v%{version}.tar.gz

%description
C preprocessor implementations of a hash table and a linked list

%prep
%autosetup -n uthash-%{version}

%install
install -dm755 %{buildroot}%{_includedir}
cp src/*.h %{buildroot}%{_includedir}

%files
%{_includedir}/*.h

%changelog
* Mon Nov 14 2022 Ole Ernst <ole.ernst@nmsprime.com> - 2.3.0-1
- Initial RPM release
