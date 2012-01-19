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

# Test fMBT/examples/*

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.examples.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

##########################################
# Run the test

teststep "testing example/c++-unittest..."
FAILED=0
MYDIR=$(pwd)
cd ../../examples/c++-unittest
make clean >> $LOGFILE || {
    echo "failed:the first 'make clean' failed in $(pwd)" >> $LOGFILE
    FAILED=1
}

[ $FAILED == 1 ] || make >> $LOGFILE || {
    echo "failed: 'make' failed in $(pwd)" >> $LOGFILE
    FAILED=1
}

[ $FAILED == 1 ] || {
    if [ "$(fmbt-log test.log | tail -n 1)" != "pass" ]; then
        echo "failed: fmbt-log test.log last line is not 'pass'" >> $LOGFILE
        FAILED=1
    fi
}

[ $FAILED == 1 ] || make clean >> $LOGFILE || {
    echo "failed: the second 'make clean' failed in $(pwd)" >> $LOGFILE
    FAILED=1
}

[ $FAILED == 1 ] || make FAULTY=1 >> $LOGFILE || {
    echo "failed: 'make FAULTY=1' exited with an error" >> $LOGFILE
    FAILED=1
}

[ $FAILED == 1 ] || {
    if [ "$(fmbt-log test.log | tail -n 1)" != "fail" ]; then
        echo "failed: fmbt-log test.log last line is not 'fail'" >> $LOGFILE
        FAILED=1
    fi
}
cd "$MYDIR"
if [ $FAILED == 1 ]; then testfailed
else testpassed; fi
