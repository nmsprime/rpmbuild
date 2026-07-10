%global __strip /bin/true

Name: nmsprime-inframon-remote-poller
Version: 0.0.2
Release: 1
Summary: A CLI tool to communicate with main NMS Prime

Group: Applications/Communications
License: Custom
URL: https://github.com/nmsprime/inframon-remote-poller

BuildRequires: composer git php-cli
Requires: telegraf

%description
Remote polling agent for Inframon NMS. Connects to NMS Prime infrastructure monitoring to collect and relay metrics from remote sites.

%prep
git clone git@github.com:nmsprime/inframon-remote-poller.git
cd inframon-remote-poller

cat << EOF > inframon-remote-poller-subscribe.service
[Unit]
Description=Inframon Remote Poller - WebSocket Subscriber
After=network.target

[Service]
Environment="LOG_LEVEL=info"
ExecStart=/usr/bin/inframon-remote-poller subscribe
User=telegraf
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > inframon-remote-poller-queue.service
[Unit]
Description=Inframon Remote Poller - Queue Worker
After=network.target

[Service]
Environment="LOG_LEVEL=info"
ExecStart=/usr/bin/inframon-remote-poller queue:work
User=telegraf
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > inframon-remote-poller.conf
remote_host=nms.example.com
remote_port=8080
skip_ssl_verification=false
uuid=00000000-0000-0000-0000-000000000000

EOF

cat << EOF > inframon-remote-poller-cron.conf
*/5 * * * * telegraf /usr/bin/inframon-remote-poller sync:config > /dev/null 2>&1
EOF

cat << EOF > sudoers
Defaults:telegraf        !requiretty

telegraf ALL=(root) NOPASSWD: /usr/bin/systemctl restart telegraf.service
EOF

cat << EOF >> %{name}.log
%{_localstatedir}/log/nmsprime/inframon-remote-poller.log {
    daily
    rotate 30
    compress
    delaycompress
    dateext
    missingok
}
EOF

cat << EOF > path-telegraf.conf
[Service]
ExecStart=
ExecStart=/usr/bin/telegraf -config /etc/telegraf/telegraf.conf -config-directory /etc/telegraf/telegraf.nmsprime.d $TELEGRAF_OPTS
EOF

touch inframon-remote-poller.log
touch inframon-remote-poller.sqlite

%build
cd inframon-remote-poller
composer install
php inframon-remote-poller app:build --build-version=%{version}
mv builds/inframon-remote-poller builds/inframon-remote-poller.phar
./vendor/bin/phpacker build --src=./builds/inframon-remote-poller.phar --php=8.4 linux x64

%install
cd inframon-remote-poller
install -Dm755 builds/build/linux/linux-x64 %{buildroot}%{_bindir}/inframon-remote-poller
install -Dm660 inframon-remote-poller.conf %{buildroot}%{_sysconfdir}/nmsprime/inframon-remote-poller/inframon-remote-poller.conf
install -Dm644 inframon-remote-poller-cron.conf %{buildroot}%{_sysconfdir}/cron.d/inframon-remote-poller.conf
install -Dm644 inframon-remote-poller-subscribe.service %{buildroot}%{_unitdir}/inframon-remote-poller-subscribe.service
install -Dm644 inframon-remote-poller-queue.service %{buildroot}%{_unitdir}/inframon-remote-poller-queue.service
install -Dm644 path-telegraf.conf %{buildroot}%{_unitdir}/telegraf.service.d/path-telegraf.conf
install -Dm644 inframon-remote-poller.log %{buildroot}%{_localstatedir}/log/nmsprime/inframon-remote-poller.log
install -Dm660 inframon-remote-poller.sqlite %{buildroot}%{_localstatedir}/lib/nmsprime/inframon-remote-poller/inframon-remote-poller.sqlite
install -Dm644 sudoers %{buildroot}%{_sysconfdir}/sudoers.d/%{name}
install -Dm644 %{name}.log %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -d %{buildroot}%{_sysconfdir}/telegraf/telegraf.nmsprime.d

%post
# update
if [ $1 -ne 1 ]; then
sudo -u telegraf inframon-remote-poller migrate --force
systemctl daemon-reload
systemctl restart inframon-remote-poller-{subscribe,queue}.service
exit
fi
# end of update

# install
sudo -u telegraf inframon-remote-poller migrate --force
systemctl daemon-reload
systemctl enable inframon-remote-poller-{subscribe,queue}.service
echo
echo "Please run 'sudo -u telegraf inframon-remote-poller configure' and start via 'systemctl start inframon-remote-poller-{subscribe,queue}.service' (it is already enabled)"
# end of install

%files
%{_bindir}/inframon-remote-poller
%attr(775, telegraf, telegraf) %{_sysconfdir}/nmsprime/inframon-remote-poller
%attr(775, telegraf, telegraf) %{_sysconfdir}/telegraf/telegraf.nmsprime.d
%config(noreplace) %attr(600, telegraf, telegraf) %{_sysconfdir}/nmsprime/inframon-remote-poller/inframon-remote-poller.conf
%{_sysconfdir}/cron.d/inframon-remote-poller.conf
%{_sysconfdir}/logrotate.d/%{name}
%{_sysconfdir}/sudoers.d/%{name}
%{_unitdir}/inframon-remote-poller-subscribe.service
%{_unitdir}/inframon-remote-poller-queue.service
%{_unitdir}/telegraf.service.d/path-telegraf.conf
%config(noreplace) %attr(644, telegraf, telegraf) %{_localstatedir}/log/nmsprime/inframon-remote-poller.log
%attr(775, telegraf, telegraf) %{_localstatedir}/lib/nmsprime/inframon-remote-poller
%config(noreplace) %attr(600, telegraf, telegraf) %{_localstatedir}/lib/nmsprime/inframon-remote-poller/inframon-remote-poller.sqlite

%changelog
* Wed Feb 18 2026 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
