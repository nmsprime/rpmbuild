Name: nmsprime-remotepoller
Version: 1.0.0
Release: 1
Summary: Turns your machine into a NMS Prime Remote Poller

Source0: nmsprime-remotepoller.var.log.nmsprime.remotepoller.log
Source1: nmsprime-remotepoller.opt.nmsprime.remotepoller.pollercontroller.py
Source2: nmsprime-remotepoller.etc.cron.d.nmsprime-remotepoller
Source3: nmsprime-remotepoller.etc.logrotate.d.nmsprime-remotepoller
Source4: nmsprime-remotepoller.etc.nmsprime.remotepoller.conf

Group: Applications/Communications
License: GPLv3

Requires: python3
Requires: telegraf
Requires: tar
Requires: nmsprime-telegraf-data-getters

%description
Makes your machine download telegraf config from nmsprime and sending collected data to a Kafka server

%prep
# Nothing to prep

%build
# Nothing to build

%install

# first create the logfile
install -D -m 0640 %{SOURCE0} %{buildroot}/var/log/nmsprime/remotepoller.log

# add the script
install -D -m 0644 %{SOURCE1} %{buildroot}/opt/nmsprime/remotepoller/pollercontroller.py

# add config files
install -D -m 0644 %{SOURCE2} %{buildroot}/etc/cron.d/nmsprime-remotepoller
install -D -m 0644 %{SOURCE3} %{buildroot}/etc/logrotate.d/nmsprime-remotepoller
install -D -m 0640 %{SOURCE4} %{buildroot}/etc/nmsprime/remotepoller.conf

install -d -m 0755 %{buildroot}/var/cache/nmsprime
install -d -m 0750 %{buildroot}/var/cache/nmsprime/remotepoller

%files
%dir /var/cache/nmsprime/remotepoller
/var/log/nmsprime/remotepoller.log
/opt/nmsprime/remotepoller/pollercontroller.py
%config(noreplace) /etc/cron.d/nmsprime-remotepoller
%config(noreplace) /etc/logrotate.d/nmsprime-remotepoller
%config(noreplace) /etc/nmsprime/remotepoller.conf

%changelog

