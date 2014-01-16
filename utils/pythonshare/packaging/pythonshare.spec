Name:           pythonshare
Version:        0.1
Release:        0
Summary:        Persistent, shared and distributed Python namespaces

License:        LGPL
URL:            https://github.com/01org/fMBT
Source:		%{name}_%{version}.tar.gz

BuildRequires:  python

Requires:       python

%description
Pythonshare enables executing Python code and evaluating
Python expressions in namespaces in pythonshare-servers.
Includes
- pythonshare-server (daemon, host and proxy namespaces)
- pythonshare-client (commandline utility for using namespaces
  on pythonshare-servers)
- Python API for using pythonshare namespaces.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root=%{buildroot} --prefix=%{_prefix}


%files
%defattr(-,root,root,-)
%{python_sitelib}/pythonshare-%{version}-*.egg-info
%{python_sitelib}/pythonshare
%{_bindir}/%{name}-client
%{_bindir}/%{name}-server


%clean
rm -rf $RPM_BUILD_ROOT

%changelog
