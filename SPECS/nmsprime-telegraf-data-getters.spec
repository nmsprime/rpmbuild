Name: nmsprime-telegraf-data-getters
Version: 1.0
Release: 1
Summary: Data getters for various NMS Prime sensors

Group: Applications/Communications
License: GPLv3
Requires: python3

Source0: nmsprime-telegraf-data-getters

%description
Add scripts to collect data about e.g. SNTP and mail servers and provide to telegraf

# this is needed to prevent python compilation error on CentOS (#2235)
# otherwise it tries to execute %{buildroot}/opt/nmsprime/remotepoller/pollercontroller.py (using python 2.7)
# thanks to: https://github.com/scylladb/scylladb/issues/2235
%global __os_install_post    \
    /usr/lib/rpm/redhat/brp-compress \
    %{!?__debug_package:\
    /usr/lib/rpm/redhat/brp-strip %{__strip} \
    /usr/lib/rpm/redhat/brp-strip-comment-note %{__strip} %{__objdump} \
    } \
    /usr/lib/rpm/redhat/brp-strip-static-archive %{__strip} \
    %{!?__jar_repack:/usr/lib/rpm/redhat/brp-java-repack-jars} \
%{nil}

%install
install -d -m 0755 %{SOURCE0} %{buildroot}/opt/nmsprime/telegraf-data-getters
install -D -m 0644 %{SOURCE0}/*.py %{buildroot}/opt/nmsprime/telegraf-data-getters

%files
/opt/nmsprime/telegraf-data-getters

%changelog
* Wed Aug 21 2024 Patrick Reichel <patrick.reichel@nmsprime.com> - 1.0-1
- Initial RPM release
