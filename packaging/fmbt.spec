Name:           fmbt
Version:        0.12.3
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
BuildRequires:  automake autoconf libtool
%if 0%{?suse_version}
BuildRequires:  libMagick++-devel
BuildRequires:  boost-devel
%else
BuildRequires:  ImageMagick-c++-devel
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

%if 0%{?suse_version}
# implicit Magick++[56]
%else
Requires: ImageMagick-c++
%endif
Requires: ImageMagick
Requires: /usr/bin/xwd
Requires: tesseract

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

%package adapter-tizen
Summary: fMBT adapter for Tizen GUI testing through USB
Requires: %{name}-adapter-eyenfinger
Requires: %{name}-python

%description adapter-tizen
Provides fmbttizen.py, a Python library for Tizen GUI testing.
The library needs Smart Development Bridge (sdb) from Tizen SDK.

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
Requires: %{name}-adapter-tizen
Requires: %{name}-adapter-vnc
Requires: %{name}-adapter-x11
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

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT/%{_libdir}/python*/site-packages/%{name}/%{name}_cparsers.la
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
%{python_sitelib}/%{name}/%{name}-log
%{python_sitelib}/%{name}/%{name}-stats
%{python_sitelib}/%{name}/%{name}-view
%{python_sitelib}/%{name}/lsts2dot

%files coreutils
%defattr(-, root, root, -)
%{_bindir}/%{name}-aalc
%{_bindir}/%{name}-aalp
%{_bindir}/%{name}-gt
%{_bindir}/%{name}-log2lsts
%{_bindir}/%{name}-parallel
%{_bindir}/%{name}-trace-share
%{python_sitelib}/%{name}/%{name}-gt
%{python_sitelib}/%{name}/%{name}-parallel
%{python_sitelib}/%{name}/%{name}-trace-share

%files devel
%defattr(-, root, root, -)
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.hh

%files editor
%defattr(-, root, root, -)
%{_bindir}/%{name}-editor
%{_bindir}/%{name}-scripter
%{_bindir}/%{name}-gteditor
%{python_sitelib}/%{name}/%{name}-editor
%{python_sitelib}/%{name}/%{name}-scripter
%{python_sitelib}/%{name}/%{name}-gteditor

%files python
%defattr(-, root, root, -)
%dir %{python_sitelib}/%{name}
%{python_sitelib}/fmbt.py*
%{python_sitelib}/fmbtgti.py*
%{python_sitelib}/fmbtlogger.py*
%{python_sitelib}/fmbtuinput.py*
%{python_sitelib}/%{name}/lsts.py*
%{python_sitelib}/%{name}/aalmodel.py*
%{python_sitelib}/%{name}/%{name}parsers.py*
%{python_sitelib}/%{name}/%{name}_config.py*
%dir %{_libdir}/python*/site-packages/%{name}
%{_libdir}/python*/site-packages/%{name}/%{name}_cparsers.so

%files adapters-remote
%defattr(-, root, root, -)
%{_bindir}/remote_adapter_loader
%{_bindir}/remote_exec.sh
%{_bindir}/remote_pyaal
%{_bindir}/remote_python
%{python_sitelib}/%{name}/remote_pyaal
%{python_sitelib}/%{name}/remote_python

%{python_sitelib}/%{name}web.py*

%files adapter-eyenfinger
%defattr(-, root, root, -)
%{_libdir}/python*/site-packages/eye4graphics.so
%{python_sitelib}/eyenfinger.py*

%files adapter-android
%defattr(-, root, root, -)
%{python_sitelib}/fmbtandroid.py*

%files adapter-tizen
%defattr(-, root, root, -)
%{python_sitelib}/fmbttizen.py*
%{python_sitelib}/fmbttizen-agent.py*

%files adapter-vnc
%defattr(-, root, root, -)
%{python_sitelib}/fmbtvnc.py*

%files adapter-x11
%defattr(-, root, root, -)
%{python_sitelib}/fmbtx11.py*

%files doc
%defattr(-, root, root, -)
%dir %{_datadir}/doc/%{name}
%doc %{_datadir}/doc/%{name}/README
%doc %{_datadir}/doc/%{name}/*.txt
%doc %{_mandir}/man1/*.1*

%files examples
%defattr(-, root, root, -)
%dir %{_datadir}/doc/%{name}/examples
%doc %{_datadir}/doc/%{name}/examples/*

%changelog
