Name: icingaweb2-module-director
Version: 1.10.2
Release: 2
Summary: Configuration frontend for Icinga 2, integrated automation

Group: Applications/Communications
License: GPLv2
URL: https://github.com/Icinga/icingaweb2-module-director
Source0: https://github.com/Icinga/%{name}/archive/v%{version}.tar.gz
Source1: %{name}-common.tar.gz
Source2: http://www.supermicro.com/support/faqs/data_lib/FAQ_9633_SAS2IRCU_Phase_5.0-5.00.00.00.zip#/sas2ircu.zip
Source3: https://exchange.nagios.org/components/com_mtree/attachment.php?link_id=1487&cf_id=24#/TFTP-1.0.tgz
Source4: https://raw.githubusercontent.com/matteocorti/check_updates/v1.6.22/check_updates
Source5: http://nagios.manubulon.com/check_snmp_env.pl
Source6: https://raw.githubusercontent.com/justintime/nagios-plugins/master/check_mem/check_mem.pl
Source7: https://raw.githubusercontent.com/hrix/nagios-plugin-ip_conntrack/master/check_ip_conntrack.pl
Source8: https://gitlab.com/argaar/nagios-plugins/raw/master/check%20symmetra%20apc/check_apc.pl
Source9: https://raw.githubusercontent.com/melmorabity/nagios-plugin-systemd-service/master/check_systemd_service.sh

Requires: bc dhcpd-pools icinga2 icinga2-ido-pgsql icingacli icingaweb2 icingaweb2-module-incubator nagios-plugins-all
Requires: nmsprime-hfcreq nmsprime-provmon perl-Nagios-Plugin perl-Net-SNMP
Requires: perl-Readonly perl-Switch php80-php-ldap php80-php-intl rh-php73-php-process pgloader

%description
Icinga Director has been designed to make Icinga 2 configuration handling easy.
It tries to target two main audiences: 1) Users with the desire to completely
automate their datacenter 2) Sysops willing to grant their "point & click" users
a lot of flexibility. What makes Icinga Director so special is the fact that it
tries to target both of them at once.

%prep
tar xf %{_sourcedir}/v%{version}.tar.gz
rm -rf %{name}-%{version}/.git* %{name}-%{version}/.travis.yml
tar xf %{_sourcedir}/%{name}-common.tar.gz
unzip -p %{_sourcedir}/sas2ircu.zip sas2ircu_linux_x86_rel/sas2ircu > sas2ircu
tar xzf %{_sourcedir}/TFTP-1.0.tgz TFTP-1.0/check_tftp.py --strip-components 1
sed 's|^#!perl$|#!/usr/bin/env perl|' %{_sourcedir}/check_updates > check_updates
sed 's|/usr/local/nagios/libexec|/usr/lib64/nagios/plugins|;s/Net::SNMP->VERSION/version->parse(Net::SNMP->VERSION)/' %{_sourcedir}/check_snmp_env.pl > check_snmp_env.pl
cd %{name}-%{version}
patch -p1 -i ../hostgroup.patch
rm ../hostgroup.patch
sed -i 's/User=icingadirector/User=apache/' contrib/systemd/icinga-director.service

%install
install -d %{buildroot}%{_unitdir}
cp %{name}-%{version}/contrib/systemd/icinga-director.service %{buildroot}%{_unitdir}/icinga-director.service
install -d %{buildroot}%{_datarootdir}/icingaweb2/modules
mv %{name}-%{version} %{buildroot}%{_datarootdir}/icingaweb2/modules/director
install -d %{buildroot}%{_sysconfdir}/icinga2
mv conf.d %{buildroot}%{_sysconfdir}/icinga2
mv icingaweb2 %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_libdir}/nagios
mv plugins %{buildroot}%{_libdir}/nagios
cp %{_sourcedir}/check_{{mem,ip_conntrack,apc}.pl,systemd_service.sh} %{buildroot}%{_libdir}/nagios/plugins
mv check_{tftp.py,updates,snmp_env.pl} %{buildroot}%{_libdir}/nagios/plugins
install -d %{buildroot}%{_sysconfdir}/sudoers.d
mv nmsprime-icinga %{buildroot}%{_sysconfdir}/sudoers.d
install -d %{buildroot}%{_bindir}
mv sas2ircu %{buildroot}%{_bindir}

%post

######### UPDATE #########

if [ $1 -ne 1 ]; then

# If postgres DB is not yet there - move Data from mysql to postgres
# TODO: Remove all the DB conversion stuff in next version
sudo -Hiu postgres /usr/pgsql-13/bin/psql -lqt | cut -d '|' -f 1 | grep -w icinga2

if [ $? -eq 1 ]; then

sed -i 's/^db = \"mysql\"/db = \"pgsql\"/' /etc/icingaweb2/resources.ini
sed -i 's/^port =.*/port = 5432/' /etc/icingaweb2/resources.ini
sed -i 's/^charset = \".*\"/charset = \"utf8\"/' /etc/icingaweb2/resources.ini

systemctl daemon-reload
systemctl stop icinga2 icinga-director

# Prepare DB conversion statements for pgloader
echo "LOAD DATABASE
  FROM mysql://psqlconverter@localhost/<db>
  INTO postgresql:///<db>
  WITH data only, batch rows = 5000, prefetch rows = 5000
  CAST
    type tinyint to smallint
  BEFORE LOAD DO \$\$ ALTER SCHEMA public RENAME TO <db>; \$\$
  AFTER LOAD DO \$\$ DROP SCHEMA IF EXISTS public; \$\$,
    \$\$ ALTER SCHEMA <db> RENAME TO public; \$\$;" > /tmp/db.load

# Create DBs and user
for db in icinga2 icingaweb2 director; do
  cmdFile="/tmp/$db.load";
  sed "s/<db>/$db/" /tmp/db.load > $cmdFile
  echo "INFO: Create postgres database '$db'"
  sudo -u postgres createdb $db

  psw=$(awk "/\[$db\]/{flag=1;next}/\[/{flag=0}flag" /etc/icingaweb2/resources.ini | grep "^password" | sort | cut -d '=' -f2 | xargs)
  user=${db}user
  sudo -Hiu postgres /usr/pgsql-13/bin/psql -c "CREATE USER $user PASSWORD '$psw'"
  echo $user

  if [ "$db" = 'icinga2' ]; then
    sed -i -e 's|//user =.*|user = "icinga2user"|' \
      -e "s|//password =.*|password = \"$psw\"|" \
      -e 's|//host|host|' \
      -e 's|//database =.*|database = "icinga2"|' /etc/icinga2/features-available/ido-pgsql.conf
    chown icinga:icinga /etc/icinga2/features-available/ido-pgsql.conf
    icinga2 feature enable ido-pgsql
    icinga2 feature disable ido-mysql
  fi
done

# Create DB Schema
sudo -Hiu postgres /usr/pgsql-13/bin/psql icinga2 < /usr/share/icinga2-ido-pgsql/schema/pgsql.sql
sudo -Hiu postgres /usr/pgsql-13/bin/psql icinga2 << EOF
  ALTER TABLE icinga_objects ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
  ALTER TABLE icinga_hoststatus ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
  ALTER TABLE icinga_servicestatus ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
EOF

sudo -Hiu postgres /usr/pgsql-13/bin/psql icingaweb2 < /usr/share/icingaweb2/schema/pgsql.schema.sql
sudo -Hiu postgres /usr/pgsql-13/bin/psql director -c "CREATE EXTENSION pgcrypto;"      # Improve performance
icingacli director migration run

read -r -a credentials <<< $(grep '^ROOT_DB_USERNAME\|^ROOT_DB_PASSWORD=' /etc/nmsprime/env/root.env | cut -d '=' -f2)
if ! mysql -u "${credentials[0]}" -p"${credentials[1]}" -e "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = 'psqlconverter')"; then
  mysql -u "${credentials[0]}" -p"${credentials[1]}" --exec='Create user psqlconverter; GRANT select ON *.* TO psqlconverter;'
fi

# Convert DBs (copy data) and Set user permissions
for db in icinga2 icingaweb2 director; do
  cmdFile="/tmp/$db.load";
  sudo -u postgres pgloader -q $cmdFile

  user=${db}user
  sudo -Hiu postgres /usr/pgsql-13/bin/psql $db -c "
    ALTER ROLE $user set search_path to 'public';
    ALTER ROLE postgres set search_path to 'public';
    GRANT USAGE ON SCHEMA public TO $user;
    GRANT ALL PRIVILEGES ON ALL Tables in schema public TO $user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $user;"
done

sudo -Hiu postgres /usr/pgsql-13/bin/psql director << "EOF"
  UPDATE import_source_setting set setting_value = 'SELECT CONCAT(NE.id, ''_'', NE.name) AS id,
  CONCAT(NP.id, ''_'', NP.name) AS parent_id_name,
  NP.base_type_id as parent_type,
  NE.name, NE.parent_id AS parent,
  NE.ip, NE.port,
  CASE WHEN NE.community_ro <> '''' THEN NE.community_ro ELSE (SELECT ro_community FROM nmsprime.provbase WHERE deleted_at IS NULL) END AS ro_community,
  CASE WHEN NT.base_type_id = 2 THEN 1 ELSE NT.base_type_id END AS netelementtype_id, NT.vendor,
  CASE WHEN NE.id IN (SELECT DISTINCT netelement_id FROM nmsprime.modem WHERE modem.deleted_at IS NULL) THEN 1 ELSE 0 END AS isbubble
FROM nmsprime.netelement AS NE
  JOIN nmsprime.netelementtype AS NT ON NE.netelementtype_id = NT.id
  LEFT JOIN nmsprime.netelement AS NP ON NE.parent_id = NP.id
WHERE NT.base_type_id between 2 and 10 and NT.base_type_id not in (8, 9) AND NE.deleted_at IS NULL;'
  WHERE source_id = 1 and setting_name = 'query';

  INSERT INTO sync_property (id, rule_id, source_id, source_expression, destination_field, priority, filter_expression, merge_policy) VALUES
    (1,1,1,'generic-host-director','import',1,NULL,'override'),
    (2,1,1,'${ip}','address',2,NULL,'override'),
    (3,1,1,'${name}','display_name',3,NULL,'override'),
    (4,1,1,'${parent}','vars.parents',4,NULL,'override'),
    (5,1,1,'${netelementtype_id}','vars.netelementtype_id',5,NULL,'override'),
    (6,1,1,'${ro_community}','vars.ro_community',6,NULL,'override'),
    (7,1,1,'${netelementtype_id}','groups',7,NULL,'override'),
    (8,1,1,'${vendor}','vars.vendor',8,NULL,'override'),
    (9,1,1,'${port}','vars.port',9,NULL,'override'),
    (10,1,1,'${isbubble}','vars.isBubble',10,NULL,'override'),
    (11,1,1,'${parent_id_name}','vars.parent_id_name',11,NULL,'override'),
    (12,1,1,'${parent_type}','vars.parent_type',12,NULL,'override')
  ON CONFLICT (id) DO UPDATE SET
    id = excluded.id,
    rule_id = excluded.rule_id,
    source_id = excluded.source_id,
    source_expression = excluded.source_expression,
    destination_field = excluded.destination_field,
    priority = excluded.priority,
    filter_expression = excluded.filter_expression,
    merge_policy = excluded.merge_policy;

  UPDATE icinga_host
  SET check_command_id = icinga_command.id
  FROM (SELECT id FROM icinga_command WHERE object_name='hostalive') AS icinga_command
  WHERE object_name = 'generic-host-director';
EOF

fi
# end of DB switch

if icingacli director migration pending ; then
  echo "Running Icinga Migrations"
  icingacli director migration run
else
  echo "No Migration Necessary"
fi

nmsprime_sec=$(awk '/\[nmsprime\]/{flag=1;next}/\[/{flag=0}flag' /etc/icingaweb2/resources.ini)
nmsprime_name=$(grep 'dbname' <<< "$nmsprime_sec" | cut -d'=' -f2 | tr -d "\"'" | xargs)

hostgroupquery="SELECT id, name FROM nmsprime.netelementtype WHERE (parent_id = 0 OR parent_id IS NULL) and id not in (8) AND id <= 10;"
sudo -Hiu postgres /usr/pgsql-13/bin/psql -d $nmsprime_name -c "$hostgroupquery" | tail -n +3 | head -n-2 | while read id name; do
  icingacli director hostgroup exists "$id" > /dev/null
  if [ $? -eq 0 ]; then
    continue
  fi
  icingacli director hostgroup create "$id" --json "{\"display_name\":\"$name\"}"
done

grep -q 'http_port' /etc/icinga2/conf.d/hosts.conf || sed -i 's|http_ssl = "true"|http_ssl = "true"\n    http_port = "8080"|' /etc/icinga2/conf.d/hosts.conf
grep -q 'vars.procs_warning' /etc/icinga2/conf.d/hosts.conf || sed -i '/import "generic-host"/a\ \ vars.procs_warning = "500"' /etc/icinga2/conf.d/hosts.conf

systemctl daemon-reload
systemctl restart icinga2
# TODO: Remove?
systemctl enable icinga-director
systemctl restart icinga-director
exit 0
fi
# end of update

######### INSTALL #########

sql_root_psw=$(grep ROOT_DB_PASSWORD /etc/nmsprime/env/root.env | cut -d'=' -f2)
sql_nmsprime_psw=$(grep DB_PASSWORD /etc/nmsprime/env/global.env | cut -d'=' -f2)
sql_icinga2_psw=$(pwgen 12 1)
sql_icingaweb2_psw=$(pwgen 12 1)
sql_director_psw=$(pwgen 12 1)
icingaweb2_psw='admin'
cmdtransport_api_psw=$(pwgen 12 1)
director_api_psw=$(pwgen 12 1)
phone_api_psw=$(pwgen 12 1)

sed -i 's|http_uri = "/"|http_uri = "/nmsprime"\n    http_ssl = "true"\n    http_port = "8080"|' /etc/icinga2/conf.d/hosts.conf
sed -i '/import "generic-host"/a\ \ vars.procs_warning = "300"' /etc/icinga2/conf.d/hosts.conf

sudo -u postgres createdb icinga2

sudo -Hiu postgres /usr/pgsql-13/bin/psql icinga2 < /usr/share/icinga2-ido-pgsql/schema/pgsql.sql
sudo -Hiu postgres /usr/pgsql-13/bin/psql icinga2 << EOF
  ALTER TABLE icinga_objects ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
  ALTER TABLE icinga_hoststatus ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
  ALTER TABLE icinga_servicestatus ADD created_at TIMESTAMP NULL, ADD updated_at TIMESTAMP NULL, ADD deleted_at TIMESTAMP NULL;
EOF

sudo -Hiu postgres /usr/pgsql-13/bin/psql icinga2 -c "
  CREATE USER icinga2user PASSWORD '$sql_icinga2_psw';
  GRANT ALL PRIVILEGES ON ALL Tables in schema public TO icinga2user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO icinga2user;
"

sed -i -e 's|//user =.*|user = "icinga2user"|' \
  -e "s|//password =.*|password = \"$sql_icinga2_psw\"|" \
  -e 's|//host|host|' \
  -e 's|//database =.*|database = "icinga2"|' /etc/icinga2/features-available/ido-pgsql.conf
chown icinga:icinga /etc/icinga2/features-available/ido-pgsql.conf

sqlCactiPsw=$(grep CACTI_DB_PASSW /etc/nmsprime/env/provmon.env | cut -d '=' -f2)
sed -i "s/vars.mysql_password = \"<mysql_cacti_psw>\"/vars.mysql_password = \"$sqlCactiPsw\"/" /etc/icinga2/conf.d/nmsprime-services.conf
sed -i "s/vars.pgsql_password = \"<pgsql_icinga2_psw>\"/vars.pgsql_password = \"$sql_icinga2_psw\"/" /etc/icinga2/conf.d/nmsprime-services.conf

systemctl enable icinga2
systemctl start icinga2
systemctl enable php80-php-fpm
systemctl start php80-php-fpm
systemctl enable icinga-director
systemctl start icinga-director
icinga2 feature enable ido-pgsql
icinga2 feature enable command
rm -f /var/cache/icinga2/icinga2.{debug,vars}
icinga2 api setup

# Icingaweb2
sudo -u postgres createdb icingaweb2
sudo -Hiu postgres /usr/pgsql-13/bin/psql icingaweb2 < /usr/share/icingaweb2/schema/pgsql.schema.sql
echo "INSERT INTO icingaweb_user (name, active, password_hash) VALUES ('admin', 1, '$(openssl passwd -1 $icingaweb2_psw)');" | sudo -Hiu postgres /usr/pgsql-13/bin/psql icingaweb2
sudo -Hiu postgres /usr/pgsql-13/bin/psql icingaweb2 -c "
  CREATE USER icingaweb2user PASSWORD '$sql_icingaweb2_psw';
  GRANT ALL PRIVILEGES ON ALL Tables in schema public TO icingaweb2user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO icingaweb2user;
"

sed -i -e "s/^password = \"<sql_icinga2_psw>\"$/password = \"$sql_icinga2_psw\"/" \
  -e "s/^password = \"<sql_icingaweb2_psw>\"$/password = \"$sql_icingaweb2_psw\"/" \
  -e "s/^password = \"<sql_nmsprime_psw>\"$/password = \"$sql_nmsprime_psw\"/" \
  -e "s/^password = \"<sql_director_psw>\"$/password = \"$sql_director_psw\"/;" /etc/icingaweb2/resources.ini
icingacli module enable monitoring

# Director
sudo -u postgres createdb director
sudo -Hiu postgres /usr/pgsql-13/bin/psql director -c "CREATE EXTENSION pgcrypto;"      # Improve performance
sudo -Hiu postgres /usr/pgsql-13/bin/psql director -c "
  CREATE USER directoruser PASSWORD '$sql_director_psw';
  GRANT ALL PRIVILEGES ON ALL Tables in schema public TO directoruser;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO directoruser;
"

sed -i -e "s/password = \"<director_api_psw>\"/password = \"$director_api_psw\"/" \
  -e "s/password = \"<phone_api_psw>\"/password = \"$phone_api_psw\"/" \
  -e "s/password = \"<cmdtransport_api_psw>\"/password = \"$cmdtransport_api_psw\"/" /etc/icinga2/conf.d/nmsprime-api-users.conf
sed -i -e "s/^endpoint = \"<hostname>\"$/endpoint = \"$(hostname)\"/" \
  -e "s/^password = \"<director_api_psw>\"$/password = \"$director_api_psw\"/" /etc/icingaweb2/modules/director/kickstart.ini
sed -i "s/^password = \"<cmdtransport_api_psw>\"$/password = \"$cmdtransport_api_psw\"/" /etc/icingaweb2/modules/monitoring/commandtransports.ini
systemctl restart httpd
systemctl restart php80-php-fpm
icingacli module enable director
icingacli director migration run
echo "127.0.0.1 $(hostname)" >> /etc/hosts
systemctl restart icinga2
sleep 5
icingacli director kickstart run

# Replace 'REPLACE' by 'INSERT INTO' according to https://stackoverflow.com/questions/1109061/insert-on-duplicate-update-in-postgresql
sudo -Hiu postgres /usr/pgsql-13/bin/psql director << "EOF"
  INSERT INTO import_source VALUES (1,'nmsprime.netelement','id','Icinga\\Module\\Director\\Import\\ImportSourceSql','unknown',NULL,NULL,NULL)
    ON CONFLICT (id) DO UPDATE SET
      id = excluded.id,
      source_name = excluded.source_name,
      key_column = excluded.key_column,
      provider_class = excluded.provider_class,
      import_state = excluded.import_state,
      last_error_message = excluded.last_error_message,
      last_attempt = excluded.last_attempt,
      description = excluded.description;
    ;

  INSERT INTO import_source_setting VALUES (1, 'query', 'SELECT CONCAT(NE.id, ''_'', NE.name) AS id,
  CONCAT(NP.id, ''_'', NP.name) AS parent_id_name,
  NP.base_type_id as parent_type,
  NE.name, NE.parent_id AS parent,
  NE.ip, NE.port,
  CASE WHEN NE.community_ro <> '''' THEN NE.community_ro ELSE (SELECT ro_community FROM nmsprime.provbase WHERE deleted_at IS NULL) END AS ro_community,
  CASE WHEN NT.base_type_id = 2 THEN 1 ELSE NT.base_type_id END AS netelementtype_id, NT.vendor,
  CASE WHEN NE.id IN (SELECT DISTINCT netelement_id FROM nmsprime.modem WHERE modem.deleted_at IS NULL) THEN 1 ELSE 0 END AS isbubble
FROM nmsprime.netelement AS NE
  JOIN nmsprime.netelementtype AS NT ON NE.netelementtype_id = NT.id
  LEFT JOIN nmsprime.netelement AS NP ON NE.parent_id = NP.id
WHERE NT.base_type_id between 2 and 10 and NT.base_type_id not in (8, 9) AND NE.deleted_at IS NULL;'),
  (1,'resource','nmsprime');

  INSERT INTO icinga_host (object_name,object_type,check_command_id,max_check_attempts,check_interval,retry_interval) SELECT 'generic-host-director','template',id,3,'60','30' FROM icinga_command WHERE object_name='hostalive';
  INSERT INTO sync_rule VALUES (1,'syncHosts','host','override','y',NULL,NULL,'unknown',NULL,NULL,NULL);
  INSERT INTO sync_property VALUES
    (1,1,1,'generic-host-director','import',1,NULL,'override'),
    (2,1,1,'${ip}','address',2,NULL,'override'),
    (3,1,1,'${name}','display_name',3,NULL,'override'),
    (4,1,1,'${parent}','vars.parents',4,NULL,'override'),
    (5,1,1,'${netelementtype_id}','vars.netelementtype_id',5,NULL,'override'),
    (6,1,1,'${ro_community}','vars.ro_community',6,NULL,'override'),
    (7,1,1,'${netelementtype_id}','groups',7,NULL,'override'),
    (8,1,1,'${vendor}','vars.vendor',8,NULL,'override'),
    (9,1,1,'${port}','vars.port',9,NULL,'override'),
    (10,1,1,'${isbubble}','vars.isBubble',10,NULL,'override'),
    (11,1,1,'${parent_id_name}','vars.parent_id_name',11,NULL,'override'),
    (12,1,1,'${parent_type}','vars.parent_type',12,NULL,'override');
  INSERT INTO director_job VALUES (1,'nmsprime.netelement','Icinga\Module\Director\Job\ImportJob','n',300,NULL,NULL,NULL,NULL,NULL), (2,'syncHosts','Icinga\Module\Director\Job\SyncJob','n',300,NULL,NULL,NULL,NULL,NULL), (3,'deploy','Icinga\Module\Director\Job\ConfigJob','n',300,NULL,NULL,NULL,NULL,NULL);
  INSERT INTO director_job_setting VALUES (1,'run_import','y'),(1,'source_id','1'),(2,'apply_changes','y'),(2,'rule_id','1'),(3,'deploy_when_changed','y'),(3,'force_generate','n'),(3,'grace_period','600');
EOF

nmsprime_sec=$(awk '/\[nmsprime\]/{flag=1;next}/\[/{flag=0}flag' /etc/icingaweb2/resources.ini)
nmsprime_name=$(grep 'dbname' <<< "$nmsprime_sec" | cut -d'=' -f2 | tr -d "\"'" | xargs)

hostgroupquery="SELECT id, name FROM nmsprime.netelementtype WHERE (parent_id = 0 OR parent_id IS NULL) and id not in (8) AND id <= 10;"
sudo -Hiu postgres /usr/pgsql-13/bin/psql -d $nmsprime_name -c "$hostgroupquery" | tail -n +3 | head -n-2 | while read id name; do
  icingacli director hostgroup exists "$id" > /dev/null
  if [ $? -eq 0 ]; then
    continue
  fi
  icingacli director hostgroup create "$id" --json "{\"display_name\":\"$name\"}"
done

%files
%{_unitdir}/*.service
%{_datarootdir}/icingaweb2/modules/director/*
%attr(0755, -, -) %{_libdir}/nagios/plugins/*
%config(noreplace) %attr(0640, icinga, icinga) %{_sysconfdir}/icinga2/conf.d/*
%dir %attr(2770, root, icingaweb2) %{_sysconfdir}/icingaweb2/modules
%dir %attr(2770, root, icingaweb2) %{_sysconfdir}/icingaweb2/modules/director
%dir %attr(2770, root, icingaweb2) %{_sysconfdir}/icingaweb2/modules/monitoring
%config(noreplace) %attr(0660, apache, icingaweb2) %{_sysconfdir}/icingaweb2/*.ini
%config(noreplace) %attr(0660, apache, icingaweb2) %{_sysconfdir}/icingaweb2/modules/director/*.ini
%config(noreplace) %attr(0660, apache, icingaweb2) %{_sysconfdir}/icingaweb2/modules/monitoring/*.ini
%attr(0640, -, -) %{_sysconfdir}/sudoers.d/*
%attr(4755, -, -) %{_bindir}/sas2ircu

%changelog
* Tue Sep 12 2023 Ole Ernst <ole.ernst@nmsprime.com> - 1.10.2-2
- disable mysql and enable pgsql IDO feature during migration
- adjust check_command_id of generic-host-director to use the hostalive one (since the IDs change during migration)

* Tue Mar 21 2023 Christian Schramm <christian.schramm@nmsprime.com> - 1.10.2-1
- update to version 1.10.2

* Thu Mar 10 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 1.8.1-7
- use postgres DB

* Mon Feb 28 2022 Christian Schramm <christian.schramm@nmsprime.com> - 1.8.1-6
- automate Icinga Migration
- fix: add automation tasks on update

* Fri Jan 14 2022 Christian Schramm <christian.schramm@nmsprime.com> - 1.8.1-5
- remove cron/job file and use icinga systemd service
- Add deployment Job to keep nmsprime and icinga in sync

* Thu Jan 13 2022 Nino Ryschawy <nino.ryschawy@nmsprime.com> - 1.8.1-4
- fix: Add dependency rh-php-73-process for director

* Mon Jan 10 2022 Christian Schramm <christian.schramm@nmsprime.com> - 1.8.1-3
- Remove getTopNetelementType DB function and use base_type_id column instead

* Wed Oct 27 2021 Ole Ernst <ole.ernst@nmsprime.com> - 1.8.1-2
- update to version 1.8.1

* Fri Oct 08 2021 Christian Schramm <christian.schramm@nmsprime.com> - 1.8.1-1
- update dependencies to PHP 8

* Fri Dec 04 2020 Ole Ernst <ole.ernst@nmsprime.com> - 1.4.2-10
- migrate to php73

* Mon May 04 2020 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-9
- allow parent_id to be both 0 and NULL

* Tue Apr 28 2020 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-8
- remove unneeded sclo-php71-php-pecl-imagick dependency
- make sure yum is not running in parallel, due to checking both
  updates and nmsprime-update at the same time

* Fri Jan 10 2020 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-7
- allow both NULL and 0 for parent_id in netelementtype
- check services radiusd, mongod, genieacs-cwmp, genieacs-fs, genieacs-nbi

* Fri Jul 19 2019 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-6
- parent_id in netelementtype is NULL instead of 0

* Mon Dec 10 2018 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-5
- Concat id as most Icinga smartphone apps can't handle the display_name

* Fri Nov 09 2018 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-4
- Rename ms_helper to clusters making the command name more descriptive

* Mon Jul 23 2018 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-3
- Automatically add new hostgroups during update
- Import port numbers if set

* Tue Jul 03 2018 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-2
- PHP 7.1 compatibility

* Mon Nov 13 2017 Ole Ernst <ole.ernst@roetzer-engineering.com> - 1.4.2-1
- Initial RPM release
