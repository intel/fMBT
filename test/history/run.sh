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

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.history.log
rm -f $LOGFILE

if [ "$1" != "installed" ]; then
    export PATH=../../src:../../utils:$PATH
    export PYTHONPATH=../../src
fi

source ../functions.sh

##########################################
# Run the test

teststep "history: new syntax one-step tests, separate logs"
./one-step-tests.sh >> $LOGFILE 2>&1 \
    && testpassed \
    || testfailed

teststep "history: old syntax one-step tests, separate logs"
./one-step-tests_old.sh >> $LOGFILE 2>&1 \
    && testpassed \
    || testfailed


teststep "history: generating log"
fmbt history_test.conf -o 'pass=steps(1)' -l run1.log >> $LOGFILE 2>&1 || {
    testfailed
}
testpassed

teststep "history: executing body"
fmbt history_test.conf -o 'fail=steps(2)' -o 'history=log(run1.log,a:b)'  >> $LOGFILE 2>&1 || {
    testfailed
}
testpassed