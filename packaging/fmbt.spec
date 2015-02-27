Name:           fmbt
Version:        0.21
Release:        0.rc0.<CI_CNT>.<B_CNT>
Summary:        free Model-Based Testing tool

License:        LGPL
URL:            https://github.com/01org/fMBT
Source:		%{name}_%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  glib2-devel
BuildRequires:  boost-devel
BuildRequires:  ncurses-devel
BuildRequires:  libxml2-devel
BuildRequires:  flex
BuildRequires:  libedit-devel
BuildRequires:  libicu-devel
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  automake autoconf libtool
BuildRequires:  ImageMagick-devel
%if 0%{?suse_version}
BuildRequires:  boost-devel
%else
BuildRequires:  boost-regex
%endif

%if 0%{?suse_version}
Requires:       dbus-1-python
%else
Requires:       dbus-python
%endif

%description
free Model-Based Testing tool automates both generating
and executing tests.

%package core
Summary: Test generator and executor

%description core
Test generator and executor

%package utils
Summary: fMBT visualizing, staticstics, reporting and log utils
Requires: %{name}-python
Requires: python
Requires: graphviz
Requires: gnuplot
Requires: ImageMagick

%description utils
Tools for visualising models, inspecting logs, statistics and reporting

%package coreutils
Summary: GT and AAL models handling
Requires: %{name}-python
Requires: %{name}-devel

%description coreutils
Tools for handling GT and AAL models

%package devel
Summary: C++ headers

%description devel
Headers for building AAL/C++ models and native adapters

%package editor
Summary: Editor
Requires: %{name}-adapters-remote
Requires: %{name}-core
Requires: %{name}-coreutils
Requires: %{name}-utils
Requires: %{name}-adapter-android
Requires: %{name}-adapter-chromiumos
Requires: %{name}-adapter-tizen
Requires: %{name}-adapter-vnc
Requires: %{name}-adapter-windows
Requires: %{name}-adapter-x11
Requires: python-pyside

%description editor
fMBT editor and scripter

%package python
Summary: fMBT python bindings
Requires: python

%description python
Common Python libraries for various fMBT components

%package adapters-remote
Summary: fMBT remote adapters
Requires: %{name}-coreutils
%if 0%{?suse_version}
Requires:       dbus-1-python
%else
Requires: dbus-python
%endif

%description adapters-remote
Generic remote adapters for running shell script, Python expressions and Javascript

%package adapter-eyenfinger
Summary: Deprecated fMBT adapter for GUI testing, use fmbtx11 instead.
Requires: ImageMagick
Requires: tesseract
%if 0%{?suse_version}
Requires: libpng12-0
%else
Requires: libpng12
%endif

%description adapter-eyenfinger
Proof-of-concept adapter for X11 GUI testing with OCR and icon matching.
This test API is deprecated, use fmbtx11 instead.

%package adapter-android
Summary: fMBT adapter for Android GUI testing through USB
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python

%description adapter-android
Provides fmbtandroid.py, a Python library for Android GUI testing.
The library needs Android Debug Bridge (adb).

%package adapter-chromiumos
Summary: fMBT adapter for Chromium OS GUI testing
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-adapter-x11
Requires: %{name}-python
Requires: %{name}-pythonshare

%description adapter-chromiumos
Provides fmbtchromiumos.py, a Python library for Chromium OS GUI testing.

%package adapter-tizen
Summary: fMBT adapter for Tizen GUI testing through USB
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python

%description adapter-tizen
Provides fmbttizen.py, a Python library for Tizen GUI testing.
The library needs Smart Development Bridge (sdb) from Tizen SDK.

%package adapter-windows
Summary: fMBT adapter for Windows GUI testing
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python
Requires: %{name}-pythonshare

%description adapter-windows
Provides fmbtwindws.py, a Python library for Windows GUI testing.
The library connects to pythonshare server running on Windows.

%package adapter-vnc
Summary: fMBT adapter for GUI testing through VNC
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python

%description adapter-vnc
Provides fmbtvnc.py, a Python library for GUI testing through VNC.
The library needs vncdotool.

%package adapter-x11
Summary: fMBT adapter for Tizen GUI testing through USB
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python

%description adapter-x11
Provides fmbtx11.py, a Python library for X11 GUI testing.

%package pythonshare
Summary: Python RPC client and server with code mobility
Requires: python

%description pythonshare
Pythonshare enables executing Python code and evaluating
Python expressions in namespaces at pythonshare-server processes.
Includes
- pythonshare-server (daemon, both host and proxy namespaces)
- pythonshare-client (commandline utility for using namespaces
  on pythonshare-servers)
- Python API for using pythonshare namespaces.

%package doc
Summary: fMBT documentation

%description doc
fMBT documentation

%package examples
Summary: fMBT examples

%description examples
various fMBT examples

%package all
Summary: Meta package for installing all fMBT packages
Requires: %{name}-adapter-android
Requires: %{name}-adapter-chromiumos
Requires: %{name}-adapter-tizen
Requires: %{name}-adapter-vnc
Requires: %{name}-adapter-x11
Requires: %{name}-adapter-windows
Requires: %{name}-doc
Requires: %{name}-editor
Requires: %{name}-examples

%description all
Meta package for installing all fMBT packages

%prep
%setup -q
./autogen.sh

%build
%configure
make %{?_smp_mflags}


%{!?python_sitelib: %define python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%{!?python_sitearch: %define python_sitearch %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib(plat_specific=True)")}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT/%{_libdir}/python*/site-packages/eye4graphics.la

%files core
%{_bindir}/%{name}

%files utils
%defattr(-, root, root, -)
%{_bindir}/%{name}-log
%{_bindir}/%{name}-stats
%{_bindir}/%{name}-view
%{_bindir}/lsts2dot
%{_bindir}/%{name}-ucheck

%files coreutils
%defattr(-, root, root, -)
%{_bindir}/%{name}-aalc
%{_bindir}/%{name}-aalp
%{_bindir}/%{name}-debug
%{_bindir}/%{name}-gt
%{_bindir}/%{name}-log2lsts
%{_bindir}/%{name}-trace-share

%files devel
%defattr(-, root, root, -)
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.hh

%files editor
%defattr(-, root, root, -)
%{_bindir}/%{name}-editor
%{_bindir}/%{name}-scripter
%{_bindir}/%{name}-gteditor

%files python
%defattr(-, root, root, -)
%{python_sitearch}/fmbt.py*
%{python_sitearch}/fmbtgti.py*
%{python_sitearch}/fmbtlogger.py*
%{python_sitearch}/fmbtuinput.py*
%{python_sitearch}/lsts.py*
%{python_sitearch}/aalmodel.py*
%{python_sitearch}/%{name}_config.py*
%{python_sitearch}/%{name}_python-*.egg-info

%files adapters-remote
%defattr(-, root, root, -)
%{_bindir}/remote_adapter_loader
%{_bindir}/remote_exec.sh
%{_bindir}/remote_pyaal
%{_bindir}/remote_python
%{python_sitearch}/%{name}web.py*

%files adapter-eyenfinger
%defattr(-, root, root, -)
%{_libdir}/python*/site-packages/eye4graphics.so
%{python_sitearch}/eyenfinger.py*
%{python_sitearch}/fmbtpng*

%files adapter-android
%defattr(-, root, root, -)
%{python_sitearch}/fmbtandroid.py*

%files adapter-chromiumos
%defattr(-, root, root, -)
%{python_sitearch}/fmbtchromiumos.py*

%files adapter-tizen
%defattr(-, root, root, -)
%{python_sitearch}/fmbttizen.py*
%{python_sitearch}/fmbttizen-agent.py*

%files adapter-windows
%defattr(-, root, root, -)
%{python_sitearch}/fmbtwindows.py*
%{python_sitearch}/fmbtwindows_agent.py*

%files adapter-vnc
%defattr(-, root, root, -)
%{python_sitearch}/fmbtvnc.py*

%files adapter-x11
%defattr(-, root, root, -)
%{python_sitearch}/fmbtx11.py*
%{python_sitearch}/fmbtx11_conn.py*

%files pythonshare
%defattr(-, root, root, -)
%dir %{python_sitelib}/pythonshare
%{_bindir}/pythonshare-server
%{_bindir}/pythonshare-client
%{python_sitelib}/pythonshare*egg*
%{python_sitelib}/pythonshare/*.py*
%{_mandir}/man1/pythonshare-*.1*

%files doc
%defattr(-, root, root, -)
%dir %{_datadir}/doc/%{name}
%doc %{_datadir}/doc/%{name}/README
%doc %{_datadir}/doc/%{name}/*.txt
%{_mandir}/man1/fmbt*.1*
%{_mandir}/man1/remote_pyaal*.1*

%files examples
%defattr(-, root, root, -)
%dir %{_datadir}/doc/%{name}/examples
%doc %{_datadir}/doc/%{name}/examples/*

%changelog
