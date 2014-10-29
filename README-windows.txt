fMBT Windows port is under development.

Installing with fMBT-installer-winXX.exe
----------------------------------------

* Run fMBT-installer-winXX.exe.

* Install all dependencies and allow extending PATH.

* Make sure directories containing following executables are in PATH:
  - python.exe  (C:\Python27)
  - fmbt.exe (C:\Program Files (x86)\Intel\fMBT)
  - dot.exe (C:\Program Files (x86)\Graphviz2.38\bin)
  - gnuplot.exe (C:\Program Files\gnuplot\bin)


Cross-compiling fMBT-installer-win32.exe
----------------------------------------

* Run on Fedora 20:

  ./build-fMBT-installer-winXX.exe.sh

* In the case you want to build 64-bit version, install
  mingw64-packages and use mingw64-configure.
