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
    export PYTHONPATH=../../src
fi

source ../functions.sh

##########################################
# Run the test

teststep "remote_pyaal model search (push/pop)..."
cat > test.conf <<EOF
model     = "aal_remote(remote_pyaal test1.py.aal)"
adapter   = "aal_remote(remote_pyaal test1.py.aal)"
heuristic = "lookahead(3)"
coverage  = "perm(2)"
pass      = "coverage(.5)"
EOF

# search for path to execute iDec in the model:
( echo '?a2' | fmbt -i test.conf -l/dev/null 2>&1 | tee output.txt )>>$LOGFILE 2>&1
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

teststep "remote_pyaal adapter in test execution..."
MYCOUNTERLOG=$(python -c 'import mycounter; print mycounter.log_filename')
rm -f "$MYCOUNTERLOG"
fmbt test.conf 2>test.verdict | tee test.log >> $LOGFILE
if [ "$(cat test.verdict)" == "pass: coverage reached" ] &&
    ( tail -n1 "$MYCOUNTERLOG" | grep -q "dec called" ) >>$LOGFILE 2>&1; then
    testpassed
else
    testfailed
fi

teststep "remote_pyaal state tags..."
cat > test.conf <<EOF
model="aal_remote(remote_pyaal test1.py.aal)"
EOF

# search for path to execute iDec in the model:
( ( echo oem1; echo iInc; echo iInc; echo iInc; echo iInc; echo mc ) | fmbt -i test.conf -l/dev/null | tail -n 2 | tee output2.txt )>>$LOGFILE 2>&1
cat > correct2.txt <<EOF
t0:LargeValue
t1:Growing
EOF

if ! diff -u output2.txt correct2.txt >> $LOGFILE 2>&1; then
    testfailed
fi
testpassed

teststep "remote_pyaal output actions..."
cat > outputs.conf <<EOF
model   = "aal_remote(remote_pyaal -l pyaal.log outputs.aal)"
adapter = "aal_remote(remote_pyaal -l pyaal.log outputs.aal)"
heuristic = "lookahead(2)"
pass = "steps:10"
on_fail = "exit:1"
EOF
fmbt outputs.conf 2>test.verdict | tee outputs.log >> $LOGFILE
(   fmbt-log outputs.log | grep -q 'o:Txt changed' && \
    fmbt-log outputs.log | grep -q 'o:Jpg changed' && \
    fmbt-log outputs.log | grep -q 'o:Png changed' && \
    fmbt-log outputs.log | grep -q 'o:Tmp changed' && 
    testpassed
) || testfailed
