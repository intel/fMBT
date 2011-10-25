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

source ../functions.sh

cd ../..

teststep "recreating the configure file..."
autoreconf --install >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "running configure..."
./configure >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "building fmbt..."
make -j2 >> $LOGFILE 2>&1 || testfailed
testpassed
