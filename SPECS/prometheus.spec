Name: prometheus
Version: 2.54.1
Release: 1
Summary: A monitoring system and time series database

Group: Applications/Communications
License: ASL 2.0
URL: https://prometheus.io
Source: https://github.com/%{name}/%{name}/releases/download/v%{version}/%{name}-%{version}.linux-amd64.tar.gz

%description
Prometheus, a Cloud Native Computing Foundation project, is a systems and
service monitoring system. It collects metrics from configured targets at given
intervals, evaluates rule expressions, displays the results, and can trigger
alerts when specified conditions are observed.

%prep
%autosetup -c %{name}-%{version}.linux-amd64

cat << EOF > %{name}.yml
global:
  scrape_interval: 1m
  evaluation_interval: 1m
  scrape_timeout: 1m

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']
  - job_name: 'telegraf'
    static_configs:
    - targets: ['localhost:9273']
  - job_name: 'nmsprime'
    static_configs:
    - targets: ['localhost:8080']
    metrics_path: 'metrics/120'
    scheme: 'https'
    scrape_interval: 2h
    basic_auth:
        username:
        password:
    tls_config:
        insecure_skip_verify: true

alerting:
  alertmanagers:
  - static_configs:
    - targets: ['localhost:9093']
EOF

cat << EOF > %{name}.service
[Unit]
Description=Prometheus Time Series Collection and Processing Server
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/bin/prometheus \
  --config.file /etc/prometheus/prometheus.yml \
  --storage.tsdb.path /var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

%install
install -Dm644 %{name}.yml %{buildroot}%{_sysconfdir}/%{name}/%{name}.yml
install -Dm644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service
cd %{name}-%{version}.linux-amd64
install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}
install -Dm755 promtool %{buildroot}%{_bindir}/promtool
install -dm755 %{buildroot}%{_sharedstatedir}/%{name}

%pre
# Add the "prometheus" group and user, id according to archlinux
groupadd -g 210 -r %{name} 2> /dev/null || :
useradd -c "Prometheus dedicated user" -u 210 -g %{name} -s /bin/false -r %{name} 2> /dev/null || :

%files
%{_bindir}/%{name}
%{_bindir}/promtool
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.yml
%{_unitdir}/%{name}.service
%attr(0755,prometheus,prometheus) %dir %{_sharedstatedir}/%{name}

%changelog
* Tue Oct 15 2024 Ole Ernst <ole.ernst@nmsprime.com> - 2.54.1-1
- Update to v2.54.1
- Remove remote_{read,write} since promscale is deprecated

* Fri Jun 24 2022 Ole Ernst <ole.ernst@nmsprime.com> - 2.36.2-1
- Initial RPM release
