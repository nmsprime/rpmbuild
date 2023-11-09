Name: alertmanager
Version: 0.24.0
Release: 1
Summary: Prometheus Alertmanager

Group: Applications/Communications
License: ASL 2.0
URL: https://prometheus.io
Source: https://github.com/prometheus/%{name}/releases/download/v%{version}/%{name}-%{version}.linux-amd64.tar.gz
Requires: prometheus

%description
The Alertmanager handles alerts sent by client applications such as the
Prometheus server. It takes care of deduplicating, grouping, and routing them to
the correct receiver integrations such as email, PagerDuty, or OpsGenie. It also
takes care of silencing and inhibition of alerts.

%prep
%autosetup -c %{name}-%{version}.linux-amd64

cat << EOF > %{name}.yml
#global:
#  smtp_from:
#  smtp_smarthost:
#  smtp_auth_username:
#  smtp_auth_password:
route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1m
  receiver: 'null'
receivers:
#- name: 'email'
#  email_configs:
#  - to:
- name: 'null'
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

cat << EOF > %{name}.service
[Unit]
Description=Alertmanager for prometheus

[Service]
Restart=always
User=prometheus
Group=prometheus
ExecStart=/usr/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager

ExecReload=/bin/kill -HUP $MAINPID
TimeoutStopSec=20s
SendSIGKILL=no

[Install]
WantedBy=multi-user.target
EOF

%install
install -Dm644 %{name}.yml %{buildroot}%{_sysconfdir}/%{name}/%{name}.yml
install -Dm644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service
cd %{name}-%{version}.linux-amd64
install -Dm755 %{name} %{buildroot}%{_bindir}/%{name}
install -Dm755 amtool %{buildroot}%{_bindir}/amtool
install -dm755 %{buildroot}%{_sharedstatedir}/%{name}

%files
%{_bindir}/%{name}
%{_bindir}/amtool
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.yml
%{_unitdir}/%{name}.service
%attr(0755,prometheus,prometheus) %dir %{_sharedstatedir}/%{name}

%changelog
* Fri Jun 24 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.24.0-1
- Initial RPM release
