#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
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
LOGFILE=/tmp/fmbt.test.learn.log
rm -f $LOGFILE

if [ "$1" != "installed" ]; then
    export PATH=../../src:../../utils:$PATH
    export PYTHONPATH=../../src
fi

source ../functions.sh

##########################################
# Run the test

teststep "learn: execution times, avoid slow actions"
cat > times.conf <<EOF
model     = aal_remote(remote_pyaal -l times.aal.log times.aal)
adapter   = aal
heuristic = lookahead(3)
learn     = time
coverage  = perm(2)
pass      = steps(25)
on_pass   = exit(0)
on_fail   = exit(1)
on_inconc = exit(2)
EOF
fmbt -l times.log times.conf >>$LOGFILE 2>&1 || {
    echo "failed because exit status 0 expected, got $?" >>$LOGFILE
    cat times.log >>$LOGFILE
    testfailed
}
if [ "$(fmbt-log times.log | grep slow | wc -l)" -gt "6" ]; then
    # TODO: 4 should be enough, what is wrong...?
    echo "failed because expected 4 slow actions, observed:" >>$LOGFILE
    fmbt-log times.log | grep slow >>$LOGFILE
    testfailed
fi
testpassed

teststep "learn: load old times, no coverage increase"
cat > times-history.conf <<EOF
model     = aal_remote(remote_pyaal -l times.aal.log times.aal)
adapter   = aal
heuristic = lookahead(3)
learn     = time
history   = log(times.log, C)
coverage  = perm(1)
pass      = steps(6)
on_pass   = exit(0)
on_fail   = exit(1)
on_inconc = exit(2)
EOF
fmbt -l times-history.log times-history.conf >>$LOGFILE 2>&1 || {
    echo "failed because exit status 0 expected, got $?" >>$LOGFILE
    cat times-history.log >>$LOGFILE
    testfailed
}
if [ "$(fmbt-log times-history.log | grep slow | wc -l)" -gt "0" ]; then
    echo "failed because expected 0 slow actions, observed:" >>$LOGFILE
    fmbt-log times-history.log | grep slow >>$LOGFILE
    testfailed
fi
testpassed
