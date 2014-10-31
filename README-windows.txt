fMBT Windows version

Install
-------

* fMBT requires Python 2.7.

* Choose fMBT installer for the same architecture as your Python. If
  you have 32-bit Python 2.7, use fMBT-installer-win32.exe. Print
  Python architecture:

  C:\Python27> python -c "import platform; print platform.architecture()"

* Run fMBT-installer-winXX.exe.

* Let the installer install all (missing) dependencies and allow
  extending PATH.


Build
-----

* Run on Fedora 20:

  ./build-fMBT-installer-winXX.exe.sh 32
  or
  ./build-fMBT-installer-winXX.exe.sh 64

  to produce

  build-win32/fMBT-installer-win32.exe
  or
  build-win64/fMBT-installer-win64.exe.


Status
------

What is expected to work:

* fmbt (test generation and execution)

* fmbt-editor

* fmbt-scripter

* GUI test interfaces: fmbttizen and fmbtwindows


What is likely to have issues (no porting efforts yet):

* GUI test interfaces: fmbtandroid, fmbtchromiumos, fmbtvnc, fmbtrdp


What will not be ported on Windows:

* GUI test interfaces: fmbtx11
