%define __python /opt/rh/rh-python38/root/usr/bin/python
Name: netbox
Version: 3.5.4
Release: 1
Summary: The premier source of truth powering network automation.

Group: Applications/Communications
License: Apache2
URL: https://netbox.dev
Source: https://github.com/%{name}-community/%{name}/archive/refs/tags/v%{version}.tar.gz
Source2: netbox.logrotate
Source3: netbox.logfile

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
    -e "s/^BASE_PATH = ''$/BASE_PATH = 'netbox\/'/" \
    -e "s/'USER': '',/'USER': 'netbox',/" \
    -e 's/^CORS_ORIGIN_ALLOW_ALL = False$/CORS_ORIGIN_ALLOW_ALL = True/' \
    -e 's/^REMOTE_AUTH_ENABLED = False$/REMOTE_AUTH_ENABLED = True/' \
    -e 's#^LOGGING = {}$#LOGGING = {\
     "version": 1,\
     "disable_existing_loggers": False,\
     "formatters": {\
         "normal": {\
             "format": "%\(asctime\)s %\(name\)s %\(levelname\)s: %\(message\)s"\
         },\
     },\
     "handlers": {\
         "file": {\
             "level": "DEBUG",\
             "class": "logging.handlers.WatchedFileHandler",\
             "filename": "/var/log/netbox/netbox.log",\
             "formatter": "normal",\
         },\
     },\
     "loggers": {\
         "django": {\
             "handlers": ["file"],\
             "level": "WARNING",\
         },\
         "netbox": {\
             "handlers": ["file"],\
             "level": "WARNING",\
         },\
     },\
}#' \
    -i %{name}/%{name}/configuration.py

cat << EOF >> %{name}/%{name}/configuration.py

# NMS PRIME settings:

# To prevent
# Forbidden (403) – CSRF verification failed. Request aborted
# add here where your NetBox installation is reachable at
CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8080',
    'https://127.0.0.1:8080',
    # https://example.com:8080
]

# Prohibit creation of duplicate IP addresses
# Default: False
ENFORCE_GLOBAL_UNIQUE = True

# Allow to retrieve all entries at once via API (using ?limit=0)
# Default: 1000
MAX_PAGE_SIZE = None
EOF

sed -e 's/User=netbox/User=nobody/' -e 's/Group=netbox/Group=nobody/' -i contrib/*.service

%install
install -d %{buildroot}/opt
install -d %{buildroot}/etc
install -d %{buildroot}/etc/logrotate.d
install -d %{buildroot}/var
install -d %{buildroot}/var/log
install -d %{buildroot}/var/log/netbox
cd ..
cp -r %{name}-%{version} %{buildroot}/opt/%{name}
install -d %{buildroot}%{_unitdir}
cp %{name}-%{version}/contrib/*.service %{buildroot}%{_unitdir}
cp %{name}-%{version}/contrib/*.timer %{buildroot}%{_unitdir}
%{__install} -D -m 0644 %{SOURCE2} %{buildroot}/%{_sysconfdir}/logrotate.d/netbox
%{__install} -D -m 0640 %{SOURCE3} %{buildroot}/var/log/netbox/netbox.log

%files
%{_unitdir}
/opt/%{name}
%config(noreplace) /opt/%{name}/%{name}/%{name}/configuration.py
%config(noreplace) %{_sysconfdir}/logrotate.d/netbox
%config(noreplace) /var/log/netbox/netbox.log

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

    chmod -R o-rwx /var/log/netbox
    chown -R nobody:nobody /var/log/netbox

    systemctl daemon-reload
    systemctl enable netbox-housekeeping.timer
    systemctl enable --now netbox netbox-rq
fi

%changelog
* Wed Sep 20 2023 Ole Ernst <ole.ernst@nmsprime.com> - 3.5.4-1
- Initial RPM release
