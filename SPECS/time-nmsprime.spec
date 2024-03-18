Name: time-nmsprime
Version: 0.0.1
Release: 1
Summary: Time Protocol written in Rust

Group: Applications/Communications
License: Custom
URL: https://github.com/nmsprime/%{name}

BuildRequires: cargo git rust

%description
%{summary}

%prep
git clone git@github.com:nmsprime/%{name}.git

%build
cd %{name}
cargo rustc --release

cat << EOF > %{name}.service
[Unit]
Description=%{summary}
After=network.target

[Service]
ExecStart=/usr/bin/%{name}
Restart=always

[Install]
WantedBy=default.target
EOF


%install
cd %{name}
install -Dm755 target/release/%{name} %{buildroot}%{_bindir}/%{name}
install -Dm644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service

%files
%{_bindir}/%{name}
%{_unitdir}/%{name}.service

%changelog
* Fri Nov 04 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
