#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2012, 2013 Intel Corporation.
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
LOGFILE=/tmp/fmbt.test.coverage_shared.log
export PATH=../../src:../../utils:$PATH
source ../functions.sh

teststep "coverage shared, one client"

fmbt -l shared.log shared.conf >> $LOGFILE 2>&1 || {
    echo "failed because fmbt exit status 0 expected" >>$LOGFILE
    testfailed
}

sleep 0.5

if ps u -p `grep pid /tmp/fmbt.coverage_shared.trace.log|tail -1|awk '{print $NF}'` > /dev/null 2>&1; then
    echo "fmbt-trace-shared session server alive" >>$LOGFILE
    testfailed
else
    testpassed
fi

teststep "coverage shared, two clients"

fmbt -l two.log two.conf >> $LOGFILE 2>&1 || {
    echo "failed because fmbt exit status 0 expected" >>$LOGFILE
    testfailed
}

sleep 0.5

if ps u -p `grep pid /tmp/fmbt.coverage_shared.trace.log|tail -1|awk '{print $NF}'` > /dev/null 2>&1; then
    echo "fmbt-trace-shared session server alive" >>$LOGFILE
    testfailed
else
    testpassed
fi
