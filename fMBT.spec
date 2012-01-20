Name:           fMBT
Version:        0.1rc9
Release:        1%{?dist}
Summary:        free model based testing tool

License:        lgpl
URL:            https://github.com/pablovirolainen/fMBT
Source:		fmbt.tar.gz

BuildRequires:  glibc-devel
BuildRequires:  glib2-devel
BuildRequires:  boost-devel
BuildRequires:  ncurses-devel
BuildRequires:  ncurses-libs
BuildRequires:  libedit-devel
BuildRequires:  gcc-c++
BuildRequires:  pexpect
BuildRequires:  dbus-python
BuildRequires:  autoconf
BuildRequires:  automake
Requires:       dbus-python
Requires:       pexpect

%description
Free Model Based testing tool

%prep
%setup -q


%build
./autogen.sh
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%files
%{_bindir}/*
%{_includedir}
%{_libdir}
%doc



%changelog
