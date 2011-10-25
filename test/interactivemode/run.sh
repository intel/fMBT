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
LOGFILE=/tmp/fmbt.test.interactivemode.log
FMBT_BIN=../../src/fmbt

source ../functions.sh

rm -f testlog.txt

##########################################
# Run the test

teststep "create model for interactive mode test..."
./create-model.sh >>$LOGFILE 2>&1 || {
    testfailed
}
testpassed

teststep "run interactive mode mbt test..."
$FMBT_BIN -L testlog.txt test.conf >>$LOGFILE 2>&1 || {
    echo "error: fmbt returned non-zero return value: $?" >> $LOGFILE
    echo "mbt test log:     $(dirname $0)/testlog.txt" >> $LOGFILE
    echo "adapter test log: $(dirname $0)/testlog-adapter.txt" >> $LOGFILE
    testfailed
}
testpassed

##########################################
# Verify the result

teststep "check coverage..."
covered=$(awk -F\" '/coverage=/{print $4}' < testlog.txt | tail -n1)
if [ "$covered" != "1.000000" ]; then
    echo "Failed: did not achieve the required coverage." >> $LOGFILE
    testfailed
fi
testpassed
