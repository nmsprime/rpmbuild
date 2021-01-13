Name: fft-nmsprime
Version: 0.0.1
Release: 1
Summary: A highly efficient FFT used for PNM data

Group: Applications/Communications
License: GPLv3
URL: https://github.com/nmsprime/fft-nmsprime
Source: https://raw.githubusercontent.com/nmsprime/fft-nmsprime/master/src/%{name}.c

BuildRequires: gcc fftw-devel
Requires: fftw-libs-double

%description
A highly efficient FFT used for PNM data.

%build
gcc -std=c99 -s -O3 -Wall -lm -lfftw3 -o %{name} %{_sourcedir}/%{name}.c

%install
install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Mon Aug 19 2020 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
