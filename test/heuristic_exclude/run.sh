#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2012, Intel Corporation.
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
LOGFILE=/tmp/fmbt.test.heuristic.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "heuristic: generate model..."
fmbt-gt -f t1.gt -o t1.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1
}
testpassed

cat > test-defaults.conf <<EOF
model     = "lsts(t1.lsts)"
coverage  = "perm(1)"
fail      = "coverage(1)"
pass      = "no_progress(4)"
EOF

teststep "heuristic exclude"

for ACTIONMATCH in "iFilter" "'iFilter'" ".*ilter" "'iFi.*'"; do

    cp test-defaults.conf test.conf
    cat >> test.conf <<EOF
heuristic = "exclude($ACTIONMATCH, lookahead(1))"
EOF

    (echo "testing"; tail -n 1 test.conf) >> $LOGFILE 2>&1

    fmbt test.conf -l hexclude.log >>$LOGFILE 2>&1 || {
        testfailed
    }

    covered=$(awk -F\" '/coverage=/{print $4}' < hexclude.log | tail -n1)
    if [ "$covered" != "0.750000" ]; then
        echo "Failed: did not achieve the required coverage." >> $LOGFILE
        testfailed
        exit 1
    fi

    if fmbt-log hexclude.log | grep -q iFilter; then
        echo "Failed: excluded action 'iFilter' was executed" >> $LOGFILE
        testfailed
    fi
done

testpassed
