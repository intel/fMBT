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
LOGFILE=/tmp/fmbt.test.coverage.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "coverage_weight: generate model"
fmbt-gt -f t2.gt -o t2.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed

teststep "Heuristic weight"
echo 'model = "lsts:t2.lsts"' > test.conf
echo 'heuristic = "weight:test.weight"' >> test.conf
echo 'pass = "steps:5"' >> test.conf

fmbt test.conf -l weight.log >>$LOGFILE 2>&1 || {
    testfailed
}

testpassed
