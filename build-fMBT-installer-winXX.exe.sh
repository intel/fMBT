#!/bin/bash

XX=$1
WINDOWS_DEPENDENCY_MIRROR=$2

if [ "$XX" != "32" ] && [ "$XX" != "64" ]; then
    echo "This script builds fMBT-installer-win32/win64.exe on Fedora 20"
    echo "Usage: $0 <32|64> [windows-dependency-mirror-URL]"
    exit 1
fi

BUILD_OUTPUT="build-win$XX/fMBT-installer-win$XX.exe"

if [ -z "$WINDOWS_DEPENDENCY_MIRROR" ]; then
    IMAGEMAGICK_URL=ftp://ftp.fifi.org/pub/ImageMagick/ImageMagick-6.9.0-0.7z
    GRAPHVIZ_URL=http://www.graphviz.org/pub/graphviz/stable/windows/graphviz-2.38.msi
    PYTHON32_URL=https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi
    PYTHON64_URL=https://www.python.org/ftp/python/2.7.8/python-2.7.8.amd64.msi
    PYSIDE32_URL=http://ftp.vim.org/languages/qt/official_releases/pyside/PySide-1.2.2.win32-py2.7.exe
    PYSIDE64_URL=http://ftp.vim.org/languages/qt/official_releases/pyside/PySide-1.2.2.win-amd64-py2.7.exe
    GNUPLOT_URL=http://sourceforge.net/projects/gnuplot/files/gnuplot/4.6.6/gp466-win32-setup.exe
    TESSERACT_URL=https://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe
else
    IMAGEMAGICK_URL=$WINDOWS_DEPENDENCY_MIRROR/ImageMagick-6.9.0-0.7z
    GRAPHVIZ_URL=$WINDOWS_DEPENDENCY_MIRROR/graphviz-2.38.msi
    PYTHON32_URL=$WINDOWS_DEPENDENCY_MIRROR/python-2.7.8.msi
    PYTHON64_URL=$WINDOWS_DEPENDENCY_MIRROR/python-2.7.8.amd64.msi
    PYSIDE32_URL=$WINDOWS_DEPENDENCY_MIRROR/PySide-1.2.2.win32-py2.7.exe
    PYSIDE64_URL=$WINDOWS_DEPENDENCY_MIRROR/PySide-1.2.2.win-amd64-py2.7.exe
    GNUPLOT_URL=$WINDOWS_DEPENDENCY_MIRROR/gp466-win32-setup.exe
    TESSERACT_URL=$WINDOWS_DEPENDENCY_MIRROR/tesseract-ocr-setup-3.02.02.exe
fi

# Install build dependencies
if [ "$(whoami)" == "root" ]; then
    SUDO=""
else
    SUDO="sudo"
fi
$SUDO yum -y install dh-autoreconf flex mingw$XX-gettext mingw$XX-expat mingw$XX-winpthreads mingw$XX-dbus-glib mingw$XX-filesystem mingw$XX-bzip2 mingw$XX-crt mingw$XX-win-iconv mingw$XX-libffi mingw$XX-cpp mingw$XX-libxml2 mingw$XX-readline mingw$XX-gcc mingw$XX-dbus mingw32-nsis mingw$XX-headers mingw$XX-termcap mingw$XX-boost mingw$XX-pkg-config mingw$XX-glib2 mingw$XX-gcc-c++ mingw$XX-zlib mingw$XX-libpng mingw-filesystem-base wget p7zip

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
            wget -nc $IMAGEMAGICK_URL
            7za x *.7z || { echo extracting ImageMagick failed; exit 1; }
            cd $(basename *.7z .7z)
                mingw$XX-configure --with-x=no && make && $SUDO make install
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

FMBT_VERSION=$(awk '/^FMBT_VERSION = /{print $3}' < Makefile)
FMBTBUILDINFO=$(awk '/^FMBTBUILDINFO = /{print $3}' < Makefile)

# Try to get commit count since the last release (tag) to untagged builds
if [ ! -z "$FMBTBUILDINFO" ]; then
    COMMITCOUNT=$(git log $(git describe --tags --abbrev=0)..HEAD --oneline | wc -l)
    if [ ! -z "$COMMITCOUNT" ]; then
        FMBTBUILDINFO="-$COMMITCOUNT$FMBTBUILDINFO"
    fi
fi

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
wget -nc $GRAPHVIZ_URL
eval wget -nc \$PYTHON${XX}_URL
eval wget -nc \$PYSIDE${XX}_URL
wget -nc $GNUPLOT_URL
wget -nc $TESSERACT_URL

# Create $BUILD_OUTPUT
makensis fmbt.nsis

cd ..

# Print result
echo ""
if [ -f "$BUILD_OUTPUT" ]; then
    BUILD_OUTPUT_VER="${BUILD_OUTPUT/.exe/-$FMBT_VERSION$FMBTBUILDINFO.exe}"
    mv "$BUILD_OUTPUT" "$BUILD_OUTPUT_VER"
    echo "Success, result:"
    echo "$BUILD_OUTPUT_VER"
    exit 0
else
    echo "build failed."
    exit 1
fi
