Name: fft-nmsprime
Version: 0.0.1
Release: 1
Summary: A highly efficient FFT used for PNM data

Group: Applications/Communications
License: GPLv3
URL: https://github.com/nmsprime/fft-nmsprime

BuildRequires: gcc fftw-devel git
Requires: fftw-libs-double

%description
A highly efficient FFT used for PNM data.

%prep
git clone git@github.com:nmsprime/%{name}.git

%build
gcc -std=c99 -s -O3 -Wall -lm -lfftw3 -o %{name}/%{name} %{name}/src/%{name}.c

%install
install -Dm755 %{name}/%{name} %{buildroot}%{_bindir}/%{name}

%files
%{_bindir}/%{name}

%changelog
* Mon Aug 19 2020 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
