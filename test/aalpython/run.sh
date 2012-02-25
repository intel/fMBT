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


# This test tests remote model and AAL/Python

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.aalpython.log
rm -f $LOGFILE

if [ "$1" != "installed" ]; then
    export PATH=../../src:../../utils:$PATH
fi

source ../functions.sh

##########################################
# Run the test

teststep "remote_pymodel search (push/pop)"
cat > test.conf <<EOF
model="remote: remote_pymodel test1.py.aal"
EOF

# search for path to execute iDec in the model:
( echo '?a2' | fmbt -i delme.conf -l/dev/null 2>&1 | tee output.txt )>>$LOGFILE 2>&1
cat > correct.txt <<EOF
Path to execute action iDec:
iInc
iInc
iInc
iChangeDirection
EOF

if ! diff -u output.txt correct.txt >> $LOGFILE 2>&1; then
    testfailed
fi
testpassed


teststep "remote_pymodel state tags"
cat > test.conf <<EOF
model="remote: remote_pymodel test1.py.aal"
EOF

# search for path to execute iDec in the model:
( ( echo oem1; echo iInc; echo iInc; echo iInc; echo iInc; echo mc ) | fmbt -i delme.conf -l/dev/null | tail -n 2 | tee output2.txt )>>$LOGFILE 2>&1
cat > correct2.txt <<EOF
t0:LargeValue
t1:Growing
EOF

if ! diff -u output2.txt correct2.txt >> $LOGFILE 2>&1; then
    testfailed
fi
testpassed
