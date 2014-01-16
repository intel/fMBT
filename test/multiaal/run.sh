#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2012, Intel Corporation.
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

# Test multiple aal model in the model and adapter...

##########################################
# Setup test environment

cd "$(dirname "$0")"
TESTDIR=$(pwd)
LOGFILE=/tmp/fmbt.test.multiaal.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

##########################################
# Run the test

FAILED=0
MYDIR=$(pwd)

teststep "building aal models without failure"

make  >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}

testpassed

teststep "Testing..."

fmbt test.conf -l multiaal.log >>$LOGFILE 2>&1 || {
    testfailed
}

testpassed

teststep "building aal models with failure"
make clean  >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}

FAULTY=1 make  >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}

testpassed

teststep "Testing..."

fmbt test_fail.conf -l multiaal_fail.log >>$LOGFILE 2>&1 || {
    testfailed
}

testpassed