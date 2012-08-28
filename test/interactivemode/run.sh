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

# This tests fMBT interactive mode (fmbt -i) commands.
# See create_model.sh for more details.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.interactivemode.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

rm -f testlog.txt

teststep "check that Python pexpect can be found..."
python -c 'import pexpect' >>$LOGFILE 2>&1 || {
    testfailed
}
testpassed

##########################################
# Run the test

teststep "create model for interactive mode test..."
./create-model.sh >>$LOGFILE 2>&1 || {
    testfailed
}
testpassed

teststep "run interactive mode mbt test..."
fmbt -L testlog.txt test.conf >>$LOGFILE 2>&1 || {
    echo "error: fmbt returned non-zero return value: $?" >> $LOGFILE
    echo "mbt test log:     $(dirname $0)/testlog.txt" >> $LOGFILE
    echo "adapter test log: $(dirname $0)/testlog-adapter.txt" >> $LOGFILE
    testfailed
    exit 1
}
testpassed

##########################################
# Verify the result

teststep "check coverage..."
covered=$(awk -F\" '/coverage=/{print $4}' < testlog.txt | tail -n1)
if [ "$covered" != "1.000000" ]; then
    echo "Failed: did not achieve the required coverage." >> $LOGFILE
    testfailed
    exit 1
fi
testpassed

teststep "interactive breakpoints and continue..."
fmbt -l breakpoints.log breakpoints.conf >> $LOGFILE 2>&1 || {
    echo "non-zero return value from fmbt" >> $LOGFILE
    echo "fmbt log: $(dirname $0)/breakpoints.log" >> $LOGFILE
    echo "adapter log: $(dirname $0)/breakpoints.aal.log" >> $LOGFILE
    testfailed
    exit 1
}
testpassed
