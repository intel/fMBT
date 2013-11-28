#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2011, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

LOGFILE=/tmp/fmbt.test.build.txt

rm -f "$LOGFILE"

cd "$(dirname "$0")"

SKIP_PATH_CHECKS=1
source ../functions.sh

cd ../..

teststep "running autogen.sh..."
./autogen.sh >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "running configure..."
./configure >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "building fmbt..."
nice make -j4 >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "making source package..."
make dist >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "building from source package..."
rm -rf fmbt.test.build                      >> $LOGFILE 2>&1 || testfailed
mkdir fmbt.test.build && cd fmbt.test.build >> $LOGFILE 2>&1 || testfailed
tar xzfv ../fmbt-*.tar.gz                   >> $LOGFILE 2>&1 || testfailed
cd fmbt-*                                   >> $LOGFILE 2>&1 || testfailed
./configure                                 >> $LOGFILE 2>&1 || testfailed
nice make -j4                               >> $LOGFILE 2>&1 || testfailed
cd ../..                                    >> $LOGFILE 2>&1 || testfailed
rm -rf fmbt.test.build                      >> $LOGFILE 2>&1 || testfailed
testpassed
