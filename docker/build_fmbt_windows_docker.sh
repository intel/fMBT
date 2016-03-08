#!/bin/bash

if [ "$1" == "32" ]; then
    ARCH=32
elif [ "$1" == "64" ]; then
    ARCH=64
else
    echo "Usage: $0 <32|64>"
    echo "builds 32 or 64-bit Windows installer"
    exit 1
fi

mkdir -p build-win$ARCH
docker build --no-cache=true -t fmbt_fedora .
docker run -i -v ${PWD}/build-win$ARCH:/build-win$ARCH fmbt_fedora sh << COMMANDS
export http_proxy=$http_proxy
export https_proxy=$https_proxy
export ftp_proxy=$ftp_proxy
echo Building $ARCH-bit fMBT installer
cd fMBT; ./build-fMBT-installer-winXX.exe.sh $ARCH
echo Copying binaries to host
cp build-win$ARCH/fMBT-installer-*.exe /build-win$ARCH
echo Changing owner from \$(id -u):\$(id -g) to $(id -u):$(id -u)
chown -R $(id -u):$(id -u) /build-win$ARCH
COMMANDS
