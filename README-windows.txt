fMBT Windows port is under development.

What works
----------

* GUI Test Interfaces:

  - fmbtwindows

    (tested: 32-bit Python, 32-bit ImageMagick, 64-bit Windows 8)


What does not work / has not been tested
----------------------------------------

* Core (test generator, AAL/Python runtime)

  - fmbt

  - remote_pyaal

* GUI Test Interfaces:

  - fmbandroid

  - fmbtchromiumos

  - fmbttizen

  - fmbtvnc

* Editors:

  - fmbt-editor

  - fmbt-scripter

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

  - C:\src\fmbt\utils>python setup.py bdist_wininst


* Install built package, for instance with 32-bit Python 2.7:

  - C:\src\fmbt\utils>dist\fmbt-python-VERSION-win32-py2.7.exe


Running on Windows
------------------

* Install:

  - ImageMagick (tested with prebuilt v6.8.9, 32-bit, with 16-bit colour depth):

    http://www.imagemagick.org/download/binaries/ImageMagick-6.8.9-4-Q16-x86-dll.exe

    (Let installed add utilities to system PATH, or add them manually)

  - Tesseract 3.02 or later (tested with v3.02.02, 32-bit)

    http://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe

  - Python 2 (tested with v2.7.7, 32bit):

    https://www.python.org/ftp/python/2.7.7/python-2.7.7.msi

  - fmbt-python-VERSION-*.exe (see Building for Windows)

* A script for testing that installation was successful:

---8<---

# This test uses simulated GUI Test Connection, it does not synthesize
# real user events. "screenshot.png" should contain a screenshot, and
# "icon.png" an icon on it.

import fmbtgti
d = fmbtgti.GUITestInterface()
d.setConnection(fmbtgti.SimulatedGUITestConnection(["screenshot.png"])
d.refreshScreenshot()
print "OCR detected words:", d.screenshot().dumpOcr()
print "tapBitmap returns:", d.tapBitmap("icon.png")

--->8---
