%define __jar_repack %{nil}

Name: kafka
Version: 3.5.1
Release: 1
Summary: An open-source distributed event streaming platform

Group: Applications/Communications
License: Apache-2.0
URL: https://kafka.apache.org
Source: https://downloads.apache.org/%{name}/%{version}/%{name}_2.13-%{version}.tgz
Requires: java-11-openjdk

%description
Apache Kafka is an open-source distributed event streaming platform used by
thousands of companies for high-performance data pipelines, streaming analytics,
 data integration, and mission-critical applications.

%prep
%autosetup -n %{name}_2.13-%{version}
rm -rf bin/windows
sed -i 's|dataDir=.*|dataDir=/opt/kafka/zookeeper|' config/zookeeper.properties
sed -i -e 's|log.dirs=.*|log.dirs=/var/log/kafka|' -e 's|listeners=PLAINTEXT.*|listeners=PLAINTEXT://localhost:9092|' config/server.properties
echo 'delete.topic.enable = true' >> config/server.properties

cat << EOF > zookeeper.service
[Unit]
Requires=network.target remote-fs.target
After=network.target remote-fs.target

[Service]
Type=simple
User=nobody
Environment=LOG_DIR=/var/log/kafka
ExecStart=/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties
ExecStop=/opt/kafka/bin/zookeeper-server-stop.sh
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
EOF

cat << EOF > kafka.service
[Unit]
Requires=zookeeper.service
After=zookeeper.service

[Service]
Type=simple
User=nobody
Environment=LOG_DIR=/var/log/kafka
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-abnormal

[Install]
WantedBy=multi-user.target
EOF

%install
install -d %{buildroot}%{_unitdir}
mv zookeeper.service %{buildroot}%{_unitdir}
mv kafka.service %{buildroot}%{_unitdir}
install -d %{buildroot}/opt/kafka/zookeeper
mv * %{buildroot}/opt/kafka
install -d %{buildroot}%{_localstatedir}/log/kafka

%post
# install
if [ $1 -eq 1 ]; then
  chown -R nobody:nobody /opt/kafka/zookeeper
  systemctl daemon-reload
  systemctl --now enable zookeeper.service
  systemctl --now enable kafka.service
fi

%files
/opt/kafka/*
%{_unitdir}/*.service
%attr(755, nobody, nobody) %{_localstatedir}/log/kafka

%changelog
* Mon Aug 14 2023 Ole Ernst <ole.ernst@nmsprime.com> - 3.5.1-1
- Initial RPM release
