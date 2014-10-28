#!/bin/bash
# This script builds fMBT-installer-win32.exe on Fedora 20

# Install build dependencies
sudo yum install mingw32-gettext mingw32-expat mingw32-winpthreads mingw32-dbus-glib mingw32-filesystem mingw32-bzip2 mingw32-crt mingw32-win-iconv mingw32-libffi mingw32-cpp mingw32-libxml2 mingw32-readline mingw32-gcc mingw32-dbus mingw32-nsis mingw32-headers mingw32-termcap mingw32-boost mingw32-pkg-config mingw32-glib2 mingw32-gcc-c++ mingw32-zlib mingw32-libpng mingw-filesystem-base wget p7zip

[ -f configure ] || ./autogen.sh || {
    echo "./autogen.sh failed"
    exit 1
}

mkdir build-w32; cd build-w32

[ -f fmbt.ico ] || ln ../fmbt.ico .

[ -f license.rtf ] || ln ../license.rtf .

# Build ImageMagick for win32
[ -f convert.exe ] || {
    mkdir build-magick
    cd build-magick
        if [ -z "$(find . -name convert.exe)" ]; then
            wget -nc ftp://ftp.fifi.org/pub/ImageMagick/ImageMagick-6.8.9-9.7z
            7za x *.7z || { echo extracting ImageMagick failed; exit 1; }
            cd $(basename *.7z .7z)
                mingw32-configure && make && sudo make install
	    cd ..
	fi
    cd ..
    ln "$(find build-magick -name convert.exe | grep libs)" . || {
        echo "building ImageMagick for win32 failed"
        exit 1
    }
}

# Build fMBT for win32
mingw32-configure --with-readline && make || {
    echo "building fMBT win32 failed"
    exit 1
}

cd utils
    make utils_installer || {
        echo "make utils_installer failed"
        exit 1
    }
cd ..

cd pythonshare
    make pythonshare_installer || {
        echo "make pythonshare_installer failed"
        exit 1
    }
cd ..

# Fetch dependencies to be included in the package
wget -nc http://www.graphviz.org/pub/graphviz/stable/windows/graphviz-2.38.msi
wget -nc https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi
wget -nc http://sourceforge.net/projects/gnuplot/files/gnuplot/4.6.6/gp466-win32-setup.exe
wget -nc http://ftp.vim.org/languages/qt/official_releases/pyside/PySide-1.2.2.win32-py2.7.exe
wget -nc https://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe

# Create build-w32/fMBT-installer-win32.exe
makensis fmbt.nsis
