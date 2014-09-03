fMBT Windows port is under development.

What works
----------

* GUI Test Interfaces:

  - fmbtwindows

  - fmbttizen (mobile)

* Editors:

  - fmbt-scripter

* Agent middleware:

  - pythonshare (platform for Python software agents, enables remote
    Python execution)

  (tested: 32-bit Python, 32-bit ImageMagick, 64-bit Windows 8)


What does not work / has not been tested
----------------------------------------

* Core (test generator, AAL/Python runtime)

  - fmbt

  - remote_pyaal

* GUI Test Interfaces:

  - fmbandroid

  - fmbtchromiumos

  - fmbttizen (ivi)

  - fmbtvnc

* Editors:

  - fmbt-editor

* Utilities

  - fmbt-log

  - fmbt-view

  - fmbt-stats


Building for Windows
--------------------

* Build requirements:

  - Visual C++ (tested with Visual Studio 2008 Express)

  - ImageMagick (tested with v6.8.9, 32-bit, 16bit colour depth):

    http://www.imagemagick.org/download/binaries/ImageMagick-6.8.9-4-Q16-x86-dll.exe

    (Install development libraries and header files)

  - Python 2 (tested with v2.7.7, 32bit):

    https://www.python.org/ftp/python/2.7.7/python-2.7.7.msi

  - fMBT sources, in this example under C:\src\fmbt


* Build:

  - Run "call vsvars32.bat" to setup Visual Studio variables. VS 2008 puts it in

    C:\Program files (x86)\Microsoft Visual Studio 9.0\Common7\Tools

  - If environment variable VS90COMNTOOLS is not defined, see

    http://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat

  - Run "C:\src\fmbt\utils>python setup.py bdist_wininst"

    This will create executable installer:

    C:\src\fmbt\utils\dist\fmbt-python-*.exe


* Build test agent platform:

  - Run "C:\src\fmbt\pythonshare>python setup.py bdist_wininst"

    This will create executable installer:

    C:\src\fmbt\pythonshare\dist\pythonshare-*.exe


Running on Windows
------------------

* Install:

  - ImageMagick (tested with prebuilt v6.8.9, 32-bit, with 16-bit colour depth):

    http://www.imagemagick.org/download/binaries/ImageMagick-6.8.9-4-Q16-x86-dll.exe

    (Let the installer add utilities to system PATH, or add them manually)

  - Tesseract 3.02 or later (tested with v3.02.02, 32-bit)

    http://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe

  - Python 2 (tested with v2.7.7, 32bit):

    https://www.python.org/ftp/python/2.7.7/python-2.7.7.msi

  - Pip (a Python package manager)

    Download https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py
    and run "python get-pip.py".

    If connected to Internet via a proxy, run
    "set https_proxy=http://PROXY:PORT" before "python get-pip.py".

  - PySide (Qt Python bindings)

    C:\Python27\Scripts>pip install -U PySide

  - Pythonshare

    pythonshare-*.exe (see Building for Windows / test agent platform)

    This will install Python scripts (like pythonshare-server) to

        C:\Python27\Scripts

    and libraries (like pythonshare\server.py) to

        C:\Python27\Lib\site-packages

  - fMBT

    fmbt-python-*.exe (see Building for Windows)

    This will install Python scripts (like fmbt-scripter) to

        C:\Python27\Scripts

    and libraries (like fmbtwindows.py) to

        C:\Python27\Lib\site-packages


* Test that fmbt-scripter and fmbtwindows work:

  - Launch and leave running pythonshare-server.
    This enables testing localhost with fmbtwindows.

    C:\fmbt-demo>python C:\Python27\Scripts\pythonshare-server

  - Launch fmbt-scripter:

    - C:\fmbt-demo>python C:\Python27\Scripts\fmbt-scripter example.py

    - Select File / New Windows.

    - Modify script: connect to localhost, no password:

      sut = fmbtwindows.Device("localhost")

    - Run the modified line (Run line) and press Ctrl-R to refresh screenshot.
      Screenshot should appear on the right hand side.

    - Press the "Control" button and click the screenshot. Touch event should
      be synthesized to the clicked position on actual desktop.


* You can remotely test a Windows device by installing Python and
  pythonshare on the device. Then launch pythonshare-server on the
  device with parameters --interface=all --password=PASSWORD. (See the
  fMBT GUI Testing wiki.)
