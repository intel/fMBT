==========================================
INTEL/FMBT IS ARCHIVED

github.com/intel/fMBT is archived.

Please see other forks for updates,
for instance:

github.com/askervin/fMBT
==========================================



fMBT Windows version

Install
-------

* Choose fMBT installer for the same architecture as your Python. If
  you have 32-bit Python 2.7, use fMBT-installer-win32.exe. Print
  Python architecture:

  C:\Python27> python -c "import platform; print platform.architecture()"

  If you do not have Python, the installer that you choose will install
  Python 2.7.8 for the correct architecture, among other dependencies.

* Run fMBT-installer-winXX.exe.

* Let the installer install all (missing) dependencies and allow
  extending PATH.


Build
-----

fMBT includes a script that builds Windows installer on Fedora
(build-fMBT-installer-winXX.exe.sh), and another script that builds
the installer inside Docker Fedora container on any Linux
(docker/build_fmbt_windows_docker.sh).

* Alternative 1, for Fedora users, build fMBT installer on host:

  Run

  ./build-fMBT-installer-winXX.exe.sh 32
  or
  ./build-fMBT-installer-winXX.exe.sh 64

  to produce

  build-win32/fMBT-installer-win32.exe
  or
  build-win64/fMBT-installer-win64.exe.

* Alternative 2, for any Linux user, build fMBT installer in Docker:

  Install Docker and run:

  cd docker; ./build_fmbt_windows_docker.sh 32
  or
  cd docker; ./build_fmbt_windows_docker.sh 64


Status
------

What is expected to work:

* fmbt (test generation and execution)

* fmbt-editor

* fmbt-scripter

* GUI test interfaces:

  - fmbtandroid

  - fmbtchromiumos

  - fmbttizen

  - fmbtwindows


What is likely to have issues (no porting efforts yet):

* GUI test interfaces: fmbtvnc, fmbtrdp


What is not planned to be ported on Windows:

* GUI test interfaces: fmbtx11
