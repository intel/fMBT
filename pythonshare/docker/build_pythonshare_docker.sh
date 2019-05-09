#!/bin/bash

# This is a proof-of-concept for building a tiny docker image that contains
# - pythonshare-server
# - statically linked version of Python
# - only needed parts of Python standard library for running the server

cd "$(dirname $0)"

PYTHONSHARE_DOCKER_DIR="$(pwd)"

cd ..

# Destination where to install static Python and Pythonshare
# and from which Docker filesystem will be created.
INSTALL_ROOT=${PYTHONSHARE_DOCKER_DIR}/image-rootfs

# Install prefix under INSTALL_ROOT
INSTALL_PREFIX=/usr
INSTALL_DIR=$INSTALL_ROOT/$INSTALL_PREFIX

# Sources where to find Pythonshare and Python
PYTHONSHARE_DIR=$(pwd)
if [ -z "$PYTHON_DIR" ]; then
    echo "PYTHON_DIR is not defined." >&2
    echo "Usage: PYTHON_DIR=/path/to/git/cpython $0"
    echo ""
    echo ""
    echo "If you do not have Python sources, you can fetch and use them with:"
    echo ""
    echo "git clone --depth 1 --branch 2.7 --single-branch https://github.com/python/cpython"
    echo "PYTHON_DIR=\$(pwd)/cpython $0"
    exit 1
fi
if [ ! -f "$PYTHON_DIR/configure" ]; then
    echo "Invalid PYTHON_DIR: cannot find '$PYTHON_DIR/configure'"
    exit 1
fi
if [ "$(grep ^VERSION= $PYTHON_DIR/configure)" != "VERSION=2.7" ]; then
    echo "Invalid Python version in PYTHON_DIR: branch 2.7 required"
    exit 1
fi

## Build and install static Python
cd "$PYTHON_DIR"
patch -p1 --ignore-whitespace --forward < $PYTHONSHARE_DOCKER_DIR/cpython.Modules.Setup.dist.patch
./configure LINKFORSHARED=" " LDFLAGS="-static -static-libgcc -Wl,--no-export-dynamic" CPPFLAGS="-static -fpic" --disable-shared --prefix "$INSTALL_DIR"
( nice make -j 16 install 2>&1 | tee make_static_build.log ) || {
    echo "building and installing static Python from '$PYTHON_DIR' to '$INSTALL_DIR' failed" >&2
    exit 1
}

## Build and install Pythonshare using just compiled Python
bash -c "
export PYTHONHOME=$INSTALL_DIR
export PYTHONPATH=$INSTALL_DIR/lib/python27.zip
cd \"$PYTHONSHARE_DIR\"
$INSTALL_DIR/bin/python setup.py install --prefix \"$INSTALL_DIR\"
sed -e 's:#!/usr/bin/env python2:#!$INSTALL_PREFIX/bin/python2:1' -i '$INSTALL_DIR/bin/pythonshare-server' '$INSTALL_DIR/bin/pythonshare-client'
cp ../utils/pycosh.py $INSTALL_DIR/lib/python2.7/site-packages
" || {
    echo "installing pythonshare from '$PYTHONSHARE_DIR' to '$INSTALL_DIR' failed" >&2
    exit 2
}

## Clean install directory
(
    cd "$INSTALL_DIR" || {
        echo "cannot chdir '$INSTALL_DIR', cleaning would be unsafe. stopping."
        exit 2
    }
    rm -rf "$INSTALL_DIR/include"
    rm -rf "$INSTALL_DIR/share"
    find . -name test -type d | xargs rm -rf
    find . -name tests -type d | xargs rm -rf
    find . -name '*.o' -o -name '*.a' | xargs rm -f

    # Find out which files are really needed by pythonshare-server and client
    PYTHONHOME=$INSTALL_DIR PYTHONPATH=$INSTALL_DIR/lib/python2.7 strace -e trace=file $INSTALL_DIR/bin/python $INSTALL_DIR/bin/pythonshare-server --help 2>&1 | grep -v ENOENT | awk -F'"' '/^open/{print $2}' > depends.txt
    PYTHONHOME=$INSTALL_DIR PYTHONPATH=$INSTALL_DIR/lib/python2.7 strace -e trace=file $INSTALL_DIR/bin/python $INSTALL_DIR/bin/pythonshare-client --help 2>&1 | grep -v ENOENT | awk -F'"' '/^open/{print $2}' >> depends.txt
    PYTHONHOME=$INSTALL_DIR PYTHONPATH=$INSTALL_DIR/lib/python2.7 strace -e trace=file $INSTALL_DIR/bin/python -c 'import pycosh' 2>&1 | grep -v ENOENT | awk -F'"' '/^open/{print $2}' >> depends.txt
    sed -e 's://*:/:g' < depends.txt | sort -u > depends-clean.txt
    # leave site-packages outside the standard library (that will be packed to python27.zip)
    mv "$INSTALL_DIR/lib/python2.7/site-packages" "$INSTALL_ROOT"
    # remove all unnecessary files under install dir
    find "$INSTALL_DIR/lib" | while read src; do
        src_clean=$(echo "$src" | sed -e 's://*:/:g')
        if grep -q "$src_clean" depends-clean.txt ; then
            echo "needed: '$src_clean'"
            if [ "${src_clean##*.}" == ".py" ]; then
                # remove also needed *.py sources if there is compiled *.pyc available
                [ -f ${src_clean}c ] && echo "removing $src_clean" && rm -f ${src};
                [ -f ${src_clean}o ] && echo "removing ${src_clean}o" && rm -f ${src}o;
            fi
        else
            echo "not needed: '$src'"
            rm -f "$src" "${src}c" "${src}o"
        fi
    done
    rm -f "$INSTALL_DIR/depends.txt" "$INSTALL_DIR/depends-clean.txt"
    cd lib/python2.7
    zip -r ../python27.zip .
    cd ../..
    rm -rf "$INSTALL_DIR/lib/python2.7"
    # restore site-packages to correct location
    mkdir -p "$INSTALL_DIR/lib/python2.7"
    mv "$INSTALL_ROOT/site-packages" "$INSTALL_DIR/lib/python2.7"
    strip bin/python2.7
)

## Include licences to Docker image
cp -v "$PYTHON_DIR/LICENSE" "$INSTALL_DIR/lib/python2.7/"
cp -v "$PYTHONSHARE_DIR/COPYING" "$INSTALL_DIR/lib/python2.7/site-packages/pythonshare/"
cat > "$INSTALL_ROOT/LICENSES" <<EOF
This docker image contains:

1. Pythonshare-server and Pycosh, LGPL v2.1
   parts of fMBT, see $INSTALL_PREFIX/lib/python2.7/site-packages/pythonshare/COPYING


2. A stripped version of Python 2.7, Python 2.7 license
   See $INSTALL_PREFIX/lib/python2.7/LICENSE

   Modifications:

   - Static build with a subset of native libraries included.

   - Those parts of Python standard library that are not needed by
     pythonshare-server and pycosh have been completely removed.

   - Python sources of remaining standard libraries have been removed, only
     precompiled versions are included in python27.zip.
EOF

cat > "$INSTALL_ROOT/HACKING" <<EOF
Prerequisites
=============

- git
- CPython build dependencies
- docker


Getting the latest sources
==========================

git clone --branch devel --single-branch --depth 1  https://github.com/intel/fMBT
git clone --branch 2.7 --single-branch --depth 1  https://github.com/python/cpython


Building new docker image from the sources
==========================================

PYTHON_DIR=\$(pwd)/cpython fMBT/pythonshare/docker/build_pythonshare_docker.sh

Docker image will be constructed from fMBT/pythonshare/docker/image-rootfs.
EOF

## Create docker image
cd "$PYTHONSHARE_DOCKER_DIR"
( cp "Dockerfile" "$INSTALL_ROOT" && cd "$INSTALL_ROOT" && docker build -t askervin/pythonshare-server:latest . )
echo "Docker image contents:"
echo "    $INSTALL_ROOT"
echo "Try pythonshare-server in container:"
echo "    docker run -it -p 8089:8089 askervin/pythonshare-server:latest"
