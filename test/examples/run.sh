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
TESTDIR=$(pwd)
LOGFILE=/tmp/fmbt.test.examples.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

##########################################
# Run the test

teststep "testing examples/c++-unittest..."
FAILED=0
MYDIR=$(pwd)
cd ../../examples/c++-unittest
make clean >> $LOGFILE || {
    echo "failed:the first 'make clean' failed in $(pwd)" >> $LOGFILE
    FAILED=1
}

[ $FAILED == 1 ] || make >> $LOGFILE 2>&1 || {
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

[ $FAILED == 1 ] || make FAULTY=1 >> $LOGFILE  2>&1 || {
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


teststep "testing examples/offline-test-suite..."
cd "$TESTDIR"
echo "# copy example to $TESTDIR" >>$LOGFILE 2>&1
cp -v ../../examples/offline-test-suite/{weakly-connected.gt,weakly-connected.conf,generate-all-tests} . >>$LOGFILE 2>&1 || {
    testfailed
}
rm -f test*.log
echo "# generate tests" >>$LOGFILE 2>&1
./generate-all-tests weakly-connected.conf >>$LOGFILE 2>&1 || {
    testfailed
}
echo "# check generated files" >>$LOGFILE 2>&1
if [ -f test6.log ] && [ ! -f test7.log ] && [ ! -f next-test.conf ]; then
    testpassed
else
    testfailed
fi
rm -f weakly-connected.conf weakly-connected.gt generate-all-tests test*log

teststep "testing examples/filesystemtest..."
cd "$TESTDIR"
cp -v ../../examples/filesystemtest/{README,filesystemtest.aal,filesystemtest.conf} . >>$LOGFILE 2>&1 || {
    echo "failed because: copying filesystemtest files failed" >>$LOGFILE
    testfailed
}
rm -f test.log
eval $(grep '$ fmbt ' README | tr -d '$') >>$LOGFILE 2>&1 || {
    echo "failed because: exit status 0 expected from README fmbt command" >>$LOGFILE
    testfailed
}
step_count=$(fmbt-log -f '$ax' test.log | wc -l)
if [[ $step_count -lt 40 ]] || [[ $step_count -gt 60 ]]; then
    echo "failed because: unexpected number of test steps in test.log: $step_count" >>$LOGFILE
    cat test.log >>$LOGFILE
    testfailed
fi
testpassed
