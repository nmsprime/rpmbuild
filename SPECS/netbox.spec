%define __python /opt/rh/rh-python38/root/usr/bin/python
Name: netbox
Version: 3.5.4
Release: 1
Summary: The premier source of truth powering network automation.

Group: Applications/Communications
License: Apache2
URL: https://netbox.dev
Source: https://github.com/%{name}-community/%{name}/archive/refs/tags/v%{version}.tar.gz

Requires: gcc libxml2-devel libxslt-devel libffi-devel libpq5-devel openssl-devel redhat-rpm-config rh-redis6-redis rh-python38 rh-python38-python-pip rh-python38-python-devel

%description
NetBox is the source of truth for everything on your network, from physical
components like power systems and cabling to virtual assets like IP addresses
and VLANs. Network automation and monitoring tools draw from this authoritative
plan to push out configurations and monitor changes across the enterprise.

%prep
%autosetup
cp %{name}/%{name}/configuration_example.py %{name}/%{name}/configuration.py
cp contrib/gunicorn.py .

sed -e "s/^ALLOWED_HOSTS = \[\]$/ALLOWED_HOSTS = \['*'\]/" \
    -e "s/'USER': '',/'USER': 'netbox',/" \
    -e 's/^CORS_ORIGIN_ALLOW_ALL = False$/CORS_ORIGIN_ALLOW_ALL = True/' \
    -e 's/^REMOTE_AUTH_ENABLED = False$/REMOTE_AUTH_ENABLED = True/' \
    -i %{name}/%{name}/configuration.py

cat << EOF >> %{name}/%{name}/configuration.py
CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8080',
    'https://127.0.0.1:8080',
]
EOF

sed -e 's/User=netbox/User=nobody/' -e 's/Group=netbox/Group=nobody/' -i contrib/*.service

%install
install -d %{buildroot}/opt
cd ..
cp -r %{name}-%{version} %{buildroot}/opt/%{name}
install -d %{buildroot}%{_unitdir}
cp %{name}-%{version}/contrib/*.service %{buildroot}%{_unitdir}
cp %{name}-%{version}/contrib/*.timer %{buildroot}%{_unitdir}

%files
%{_unitdir}
/opt/%{name}
%config(noreplace) /opt/%{name}/%{name}/%{name}/configuration.py

%post
if [ $1 -eq 1 ]; then
    systemctl enable --now rh-redis6-redis
    chown -R nobody /opt/netbox/netbox/{media,reports,scripts}

    export pgsql_pw=$(pwgen 16 1)
    export secret=$(pwgen 64 1)

    sudo -Hiu postgres /usr/pgsql-13/bin/psql -c 'CREATE DATABASE netbox;' -c "CREATE USER netbox WITH PASSWORD '$pgsql_pw'; ALTER DATABASE netbox OWNER TO netbox;"
    sudo -Hiu postgres /usr/pgsql-13/bin/psql netbox -c "GRANT CREATE ON SCHEMA public TO netbox;"

    sed -e "s/'PASSWORD': '',           # PostgreSQL password/'PASSWORD': '$pgsql_pw',           # PostgreSQL password/" \
        -e "s/^SECRET_KEY = ''$/SECRET_KEY = '$secret'/" \
        -i /opt/netbox/netbox/netbox/configuration.py

    source /opt/rh/rh-python38/enable
    /opt/netbox/upgrade.sh

    systemctl daemon-reload
    systemctl enable netbox-housekeeping.timer
    systemctl enable --now netbox netbox-rq
fi

%changelog
* Wed Sep 20 2023 Ole Ernst <ole.ernst@nmsprime.com> - 3.5.4-1
- Initial RPM release
