Name: nmsprime-telegraf-data-getters
Version: 1.2
Release: 1
Summary: Data getters for various NMS Prime sensors

Group: Applications/Communications
License: GPLv3
# install netmiko + paramiko == 3.5.1 via pip on the remote poller
Requires: python3 python3-ntplib python3-requests

Source0: nmsprime-telegraf-data-getters

%description
Add scripts to collect data about e.g. (S)NTP and mail servers and provide to telegraf

%install
install -d -m 0755 %{SOURCE0} %{buildroot}/opt/nmsprime/telegraf-data-getters
install -D -m 0644 %{SOURCE0}/*.py %{buildroot}/opt/nmsprime/telegraf-data-getters

%files
/opt/nmsprime/telegraf-data-getters

%changelog
* Fri Jul 10 2026 Ole Ernst <ole.ernst@nmsprime.com> - 1.2-1
- Add netelement config backup data getter

* Tue Mar 25 2025 Patrick Reichel <patrick.reichel@nmsprime.com> - 1.1-1
- Use python ntplib instead of the sntp binary (not available in Rocky 9)

* Wed Aug 21 2024 Patrick Reichel <patrick.reichel@nmsprime.com> - 1.0-1
- Initial RPM release
