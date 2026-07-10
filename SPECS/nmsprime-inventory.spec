Name: nmsprime-inventory
Version: 0.0.1
Release: 1
Summary: NMS Prime Inventory Cronjob

Group: Applications/Communications
License: Custom
BuildArch: noarch
URL: https://www.nmsprime.com

%description
This package contains the NMS Prime Inventory Cronjob.

%prep
git clone git@github.com:nmsprime/inventory-cronjob.git
cd inventory-cronjob

cat << EOF > nmsprime-inventory
0 0 1 * * root /usr/bin/php /var/www/nmsprime/artisan tinker %{_libexecdir}/nmsprime-n8n-inventory-report > /dev/null 2>&1
EOF

%install
cd inventory-cronjob
install -Dm644 nmsprime-inventory %{buildroot}%{_sysconfdir}/cron.d/nmsprime-inventory
install -Dm644 nmsprime-n8n-inventory-report %{buildroot}%{_libexecdir}/nmsprime-n8n-inventory-report

%files
%{_sysconfdir}/cron.d/nmsprime-inventory
%{_libexecdir}/nmsprime-n8n-inventory-report

%changelog
* Tue Mar 24 2026 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- initial release
