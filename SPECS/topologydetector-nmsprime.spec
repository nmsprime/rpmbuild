# crude workaround to disable python automagic byte compilation
# cp /usr/lib/rpm/brp-python-bytecompile /usr/lib/rpm/brp-python-bytecompile.bak
# ln -srf /usr/bin/true /usr/lib/rpm/brp-python-bytecompile
#
# the following options don't work:
#   %global _python_bytecompile_extra 0
#   %undefine __brp_python_bytecompile
#   %define __brp_python_bytecompile %{nil}

Name: topologydetector-nmsprime
Version: 0.0.1
Release: 1
Summary: Cisco Russia DevNet Marathon May 2020 winning solution

Group: Applications/Communications
License: MIT
URL: https://github.com/iDebugAll/devnet_marathon_endgame
Source0: https://github.com/iDebugAll/devnet_marathon_endgame/archive/4aeb72c.tar.gz
Source1: lldp.patch

BuildRequires: patch rh-python38
Requires: rh-python38
AutoReqProv: no

%description
An automated topology visualization solution for online Cisco DevNet Marathon
Finale. May 2020.

%prep
%autosetup -n devnet_marathon_endgame-4aeb72cf045ecf160e1865e31425cfce4375dee3
cat << EOF > groups.yaml
---

defaults:
    contact: info@nmsprime.com

nmsprime-group:
    username: username
    password: password
    connection_options:
        napalm:
            extras:
                optional_args:
                    secret: secret
EOF

%build
mkdir env
source /opt/rh/rh-python38/enable
python -m venv env/
source env/bin/activate
pip install -r requirements.txt
patch -p1 -i "%{_sourcedir}/lldp.patch"
sed -i 's/from markupsafe import soft_unicode/from markupsafe import soft_str as soft_unicode/' env/lib/python3.8/site-packages/jinja2/{filters,runtime,utils}.py

%install
install -d %{buildroot}/opt/%{name}
cp -r env %{buildroot}/opt/%{name}
cp generate_topology.py %{buildroot}/opt/%{name}
cp groups.yaml %{buildroot}/opt/%{name}

%files
/opt/%{name}/env/*
/opt/%{name}/generate_topology.py
%config(noreplace) %attr(0660, apache, apache) /opt/%{name}/groups.yaml

%changelog
* Mon Jul 25 2022 Ole Ernst <ole.ernst@nmsprime.com> - 0.0.1-1
- Initial RPM release
