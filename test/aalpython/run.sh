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
    fmbt-log outputs.log | grep -q 'o:Tmp changed' && \
    fmbt-log -f '$tg' outputs.log | grep -q "exists\['txt'\]" && \
    testpassed
) || testfailed

grep -q '^DATETIME' pyaal.log || {
    echo "possible fmbt.setAdapterLogTimeFormat() failure" >> $LOGFILE
    testfailed
}

teststep "remote_pyaal adapter_exception_handler..."
cat > expected-steps.txt <<EOF
iStep1
iStep2 - change handler
oOutputAction
error
EOF
fmbt adapter_exceptions.conf 2>adapter_exception_handler.stderr | fmbt-log > observed-steps.txt || {
    echo "failed because: non-zero exit status from fmbt-log: $?" >>$LOGFILE
    testfailed
}
diff -u expected-steps.txt observed-steps.txt >>$LOGFILE || {
    echo "failed because: expected-steps.txt and observed-steps.txt differ" >>$LOGFILE
    testfailed
}
if ! grep -q 'raise Exception("unrecoverable error!")' adapter_exception_handler.stderr; then
    cat adapter_exception_handler.stderr >>$LOGFILE
    echo "fails because: AAL line that raised exception not shown in stderr" >>$LOGFILE
    testfailed
fi
testpassed

teststep "remote_pyaal adapter() blocks of tags..."
fmbt tags-fail.conf 2>tags-fail.stderr >tags-fail.stdout && {
    echo "fails because: non-zero exit status from 'fmbt tags-fail.conf' expected" >>$LOGFILE
    testfailed
}
if egrep -q 'tNoSubdir|tNoDir|tDirExists' tags-fail.stderr; then
    cat tags-fail.stderr >>$LOGFILE
    echo "fails because: wrong tag(s) mentioned in stderr" >>$LOGFILE
    testfailed
fi
if ! grep -q 'tSubdirExists' tags-fail.stderr; then
    cat tags-fail.stderr >>$LOGFILE
    echo "fails because: failing tag not mentioned in stderr" >>$LOGFILE
    testfailed
fi
if ! grep -q 'tSubdirExists' tags-fail.stderr; then
    cat tags-fail.stderr >>$LOGFILE
    echo "fails because: failing tag not mentioned in stderr" >>$LOGFILE
    testfailed
fi
if ! ( grep 'tSubdirExists' tags-fail.stdout | grep -q Assertion ); then
    cat tags-fail.stdout >>$LOGFILE
    echo "fails because: Assertion failure with the tag not mentioned in stdout" >>$LOGFILE
    testfailed
fi
fmbt tags.conf 2>tags.stderr >tags.stdout || {
    echo "fails because: exit status zero expected from 'fmbt tags.conf'" >>$LOGFILE
    testfailed
}
if [ "$(wc -l < tags.stderr)" != "1" ]; then
    cat tags.stderr >>$LOGFILE
    echo "fails because: unnecessary output in stderr"
    testfailed
fi
testpassed
