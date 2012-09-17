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

teststep "Coverage paths"
echo 'model = "lsts_remote(fmbt-gt -f 'abc.gt')"' > test.conf
echo 'coverage = "uexecs(from \"iA\" to \"iB\")"' >> test.conf
echo 'pass   = "coverage(5)"' >> test.conf
echo 'heuristic = "lookahead(5)"' >> test.conf

fmbt test.conf -l paths.log >>$LOGFILE 2>&1 || {
    testfailed
}

testpassed