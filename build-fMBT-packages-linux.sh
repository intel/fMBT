#!/bin/sh
apt-get update; apt-get -y install git dpkg-dev devscripts python debhelper gcc libglib2.0-dev libboost-dev libedit-dev automake libtool libxml2-dev libmagickcore-dev libboost-regex-dev libc6-dev python-dev flex dbus python-pexpect python-dbus python-gobject graphviz imagemagick python3 dh-python
echo "detected fMBT version $(git describe --tags | sed 's/v//1')"
dch --empty -b -v $(git describe --tags | sed 's/v//1') --distribution bionic --force-distribution Build by https://gitlab.com/fmbt/fmbt_ci/

dpkg-buildpackage -us -uc
EXIT_CODE=$?
ls -la
if [ $EXIT_CODE != 0 ]; then
  mkdir logs
  mv /tmp/fmbt*.log logs
  exit ${EXIT_CODE}
fi

mkdir debs
mv ../*.deb debs
mv ../*.changes debs
mv ../*.dsc debs

cd python3share
dch --empty -b -v $(git describe --tags | sed 's/v//1') --distribution bionic --force-distribution Build by https://gitlab.com/fmbt/fmbt_ci/
dpkg-buildpackage -us -uc
EXIT_CODE=$?
ls -la
if [ $EXIT_CODE != 0 ]; then
    mv /tmp/fmbt*.log logs
    exit ${EXIT_CODE}
fi

mv ../*.deb ../debs
mv ../*.changes ../debs
mv ../*.dsc ../debs

