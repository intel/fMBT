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

teststep "remote_pyaal changing model in adapter..."
fmbt changing_model_in_adapter.conf >changing_model_in_adapter.stdout 2>changing_model_in_adapter.stderr;
exit_status=$?
if [ ! "$exit_status" == "1" ]; then
    echo "failed because: exit status 1 expected, got $exit_status" >>$LOGFILE
    testfailed
fi
fmbt-log  -f '$as -> $ax\n$tv $tr' changing_model_in_adapter.stdout > changing_model_in_adapter.observed
if ! diff -u changing_model_in_adapter.expected changing_model_in_adapter.observed >>$LOGFILE; then
    echo "failed because: expected and observed log output differ" >>$LOGFILE
    testfailed
fi
testpassed

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
if ! grep -q 'ADAPTER_EXIT: verdict=None reason=None' adapter_exceptions.aal.log; then
    cat adapter_exceptions.aal.log >>$LOGFILE
    echo "fails because: adapter_exit handler was not called properly in unrecoverable error" >>$LOGFILE
    testfailed
fi
testpassed

teststep "remote_pyaal adapter() blocks of tags..."
fmbt tags-fail.conf 2>tags-fail.stderr >tags-fail.stdout && {
    echo "fails because: non-zero exit status from 'fmbt tags-fail.conf' expected" >>$LOGFILE
    testfailed
}
if ! grep -q 'ADAPTER LOG <- ADAPTER_EXIT verdict=fail reason=verifying tags "tSubdirExists" failed.' tags.aal.log; then
    cat tags.aal.log >>$LOGFILE
    echo "fails because: tags.aal.log ADAPTER_EXIT missing or unexpected content" >>$LOGFILE
    testfailed
fi
if ! fmbt-log -f '$al' tags-fail.stdout | grep -q 'FMBT LOG <- ADAPTER_EXIT verdict=fail reason=verifying tags "tSubdirExists" failed.'; then
    fmbt-log -f '$al' tags-fail.stdout >>$LOGFILE
    echo "fails because: fmbt-log -f '\$al' shows no ADAPTER_EXIT message" >>$LOGFILE
    testfailed
fi
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
    echo "fails because: unnecessary output in stderr" >>$LOGFILE
    testfailed
fi

(cat tags-allfail.conf; echo ; echo 'disable_tag_checking') > tags-nofails.conf
if ! fmbt tags-nofails.conf 2>tags-nofails.stderr >tags-nofails.stdout; then
    echo "fails because: zero exit status from 'fmbt tags-nofails.conf' expected" >>$LOGFILE
    testfailed
fi
if grep -q Assertion tags-nofails.stdout || grep -q Assertion tags-nofails.stderr ; then
    cat tags-nofails.stderr >>$LOGFILE
    echo "fails because: 'fmbt tags-nofails.conf' found assertion failures" >>$LOGFILE
    testfailed
fi
if fmbt tags-allfail.conf 2>tags-allfail.stderr >tags-allfail.stdout; then
    echo "fails because: non-zero exit status from 'fmbt tags-allfail.conf' expected" >>$LOGFILE
    testfailed
fi
if ! grep -q 'fail: verifying tags "tNoDir" "tNoSubdir" failed.' tags-allfail.stderr; then
    cat tags-allfail.stderr >>$LOGFILE
    echo "fails because: 'fmbt tags-allfail.conf' did not notice two tags failing." >>$LOGFILE
    testfailed
fi
if ! grep Traceback tags-allfail.stdout | wc -l | grep -q 2; then
    cat tags-allfail.stdout >>$LOGFILE
    echo "fails because: 'fmbt tags-allfail.conf' did not have two tracebacks in the log." >>$LOGFILE
    testfailed
fi

(cat tags-fail.conf; echo; echo 'pass="failing_tag(include('"'tSubdirExists'"')"') >> tags-fail-inc.conf
if ! fmbt tags-fail-inc.conf 2>tags-fail-inc.stderr >tags-fail-inc.stdout; then
    echo "fails because: zero exit status from 'fmbt tags-fail.conf' expected" >>$LOGFILE
    testfailed
fi
if ! grep -q 'pass: verifying tags "tSubdirExists" failed.' tags-fail-inc.stderr; then
    cat tags-fail-inc.stderr >>$LOGFILE
    echo "fails because: 'fmbt tags-fail-inc.conf' did not pass due to failing tag" >>$LOGFILE
    testfailed
fi
(cat tags-allfail.conf; echo; ) > tags-allfail-ex.conf
cat >>tags-allfail-ex.conf <<EOF
inconc="failing_tag(exclude('tNoDir', 'tNoSubdir'))"
EOF
if fmbt tags-allfail-ex.conf 2>tags-allfail-ex.stderr >tags-allfail-ex.stdout; then
    echo "fails because: non-zero exit status from 'fmbt tags-allfail-ex.conf' expected" >>$LOGFILE
    testfailed
fi
if grep inconclusive tags-allfail-ex.stderr | egrep -q -e 'tNoDir|tNoSubdir' ; then
    echo "--- conf ---" >>$LOGFILE
    cat tags-allfail-ex.conf >>$LOGFILE
    echo >> $LOGFILE
    echo "--- stderr ---" >>$LOGFILE
    cat tags-allfail-ex.stderr >>$LOGFILE
    echo "---" >>$LOGFILE
    echo "fails because: in 'fmbt tags-allfail-ex.conf' an excluded tag stopped the test" >>$LOGFILE
    testfailed
fi
testpassed

teststep "remote_pyaal nested tags and actions"
if ! fmbt nested.conf > nested.stdout 2>nested.stderr; then
    echo "failed because expected exit status 0 from fmbt nested.conf" >>$LOGFILE
    testfailed
fi

cat > nested.expected <<EOF
iAddNonzeroElement: x is not empty; the first element of x is non-zero
iMakeFirstElementZero: x is not empty; the first element of x is zero
iClearX: can add elements
iAddZeroElement: x is not empty; the first element of x is zero
iClearX: can add elements
iAddNonzeroElement: x is not empty; the first element of x is non-zero
EOF
fmbt-log -f '$ax: $tg' nested.stdout > nested.observed 2>>$LOGFILE

if ! diff -u nested.expected nested.observed >>$LOGFILE 2>&1; then
    echo "failed because nested.observed differed from nested.expected" >>$LOGFILE
    testfailed
fi

testpassed

teststep "remote_pyaal control flow with nondet sut"
if ! fmbt controlflow.conf > controlflow.stdout 2>controlflow.stderr; then
    echo "failed because expected exit status 0 from fmbt controlflow.conf" >>$LOGFILE
    testfailed
fi
if [ "$(grep -B100 -A1 "adapter of 0 to 1" controlflow.aal.log | grep "body of 0 to 1" | wc -l)" != "2" ]; then
    echo "failed because body of 0 to 1 was not executed exactly twice before 'adapter of 0 to 1' according to controlflow.aal.log:" >>$LOGFILE
    cat controlflow.aal.log >>$LOGFILE
    testfailed
fi
if [ "$(grep -A4 'observe: action "o:x == 1"' controlflow.aal.log | grep "guard of output x == 1" | wc -l)" != "2" ]; then
    echo "failed because of missing 'guard of output x == 1' after the output that is disabled before executing its adapter" >>$LOGFILE
    testfailed
fi
if [ "$(grep -A4 'observe: action "o:x == 2"' controlflow.aal.log | grep "guard of output x == 2" | wc -l)" != "1" ]; then
    echo "failed because of extra 'guard of output x == 2' after the output that was already enabled before executing its adapter" >>$LOGFILE
    testfailed
fi
if [ "$(grep -A4 'observe: action "o:x == 3"' controlflow.aal.log | grep "guard of output x == 3" | wc -l)" != "2" ]; then
    echo "failed because of missing 'guard of output x == 3' after the output that is disabled before executing its adapter" >>$LOGFILE
    testfailed
fi
testpassed
