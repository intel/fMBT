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


cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.log2lsts.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "log2lsts: generate model"
fmbt-gt -f t1.gt -o t1.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed

teststep "Log2lsts: run"
echo 'model = "lsts(t1.lsts)"' > test.conf
echo 'coverage = "0"'         >> test.conf

fmbt test.conf -l run1.log >>$LOGFILE 2>&1 || {
    testfailed
}

testpassed

teststep "Log2lsts: create lsts from log"

fmbt-log2lts -o g1.lsts run1.log >>$LOGFILE 2>&1  || {
    testfailed
}

testpassed

teststep "Log2lsts: create lsts from log with verdict tag"

fmbt-log2lts -o g1e.lsts run1.log >>$LOGFILE 2>&1  || {
    testfailed
}

testpassed


teststep "Log2lsts: compare t1.lsts and g1.lsts"

true || {
    testfailed
}

testpassed

teststep "Log2lsts: compare t1.lsts and g1e.lsts"

true || {
    testfailed
}

testpassed

