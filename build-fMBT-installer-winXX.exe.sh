#!/bin/bash

XX=$1

if [ "$XX" != "32" ] && [ "$XX" != "64" ]; then
    echo "This script builds fMBT-installer-win32/win64.exe on Fedora 20"
    echo "Usage: $0 <32|64>"
    exit 1
fi

BUILD_OUTPUT="build-win$XX/fMBT-installer-win$XX.exe"

# Install build dependencies
sudo yum install mingw$XX-gettext mingw$XX-expat mingw$XX-winpthreads mingw$XX-dbus-glib mingw$XX-filesystem mingw$XX-bzip2 mingw$XX-crt mingw$XX-win-iconv mingw$XX-libffi mingw$XX-cpp mingw$XX-libxml2 mingw$XX-readline mingw$XX-gcc mingw$XX-dbus mingw32-nsis mingw$XX-headers mingw$XX-termcap mingw$XX-boost mingw$XX-pkg-config mingw$XX-glib2 mingw$XX-gcc-c++ mingw$XX-zlib mingw$XX-libpng mingw-filesystem-base wget p7zip

[ -f configure ] || ./autogen.sh || {
    echo "./autogen.sh failed"
    exit 1
}

mkdir build-win$XX;
rm -f "$BUILD_OUTPUT"
rm -f build-win$XX/utils/*
cd build-win$XX

[ -f fmbt.ico ] || ln ../fmbt.ico .

[ -f license.rtf ] || ln ../license.rtf .

# Build ImageMagick for win$XX
[ -f convert.exe ] || {
    mkdir build-magick
    cd build-magick
        if [ -z "$(find . -name convert.exe)" ]; then
            wget -nc ftp://ftp.fifi.org/pub/ImageMagick/ImageMagick-6.8.9-9.7z
            7za x *.7z || { echo extracting ImageMagick failed; exit 1; }
            cd $(basename *.7z .7z)
                mingw$XX-configure && make && sudo make install
	    cd ..
	fi
    cd ..
    ln "$(find build-magick -name convert.exe | grep libs)" . || {
        echo "building ImageMagick for win$XX failed"
        exit 1
    }
}

# Build fMBT for win$XX
mingw$XX-configure --with-readline && make || {
    echo "building fMBT win$XX failed"
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
if [ "$XX" == "32" ]; then
    wget -nc https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi
    wget -nc http://ftp.vim.org/languages/qt/official_releases/pyside/PySide-1.2.2.win$XX-py2.7.exe
else
    wget -nc https://www.python.org/ftp/python/2.7.8/python-2.7.8.amd64.msi
    wget -nc http://ftp.vim.org/languages/qt/official_releases/pyside/PySide-1.2.2.win-amd$XX-py2.7.exe
fi
wget -nc http://sourceforge.net/projects/gnuplot/files/gnuplot/4.6.6/gp466-win32-setup.exe
wget -nc https://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe

# Create $BUILD_OUTPUT
makensis fmbt.nsis

cd ..

# Print result
echo ""
if [ -f "$BUILD_OUTPUT" ]; then
    echo "Success, result:"
    echo "$BUILD_OUTPUT"
    exit 0
else
    echo "build failed."
    exit 1
fi
