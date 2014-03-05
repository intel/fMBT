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
LOGFILE=/tmp/fmbt.test.weight.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

cat > test-noheur.conf <<EOF
model = "lsts_remote(fmbt-gt -f model.gt)"
pass = "steps(100)"
pass = "coverage(2)"
EOF


teststep "heuristic weight: all zeros..."
(cat test-noheur.conf; echo 'heuristic = "weight(test-allzeros.weight)"') > test-allzeros.conf
fmbt test-allzeros.conf -l weight.log >>$LOGFILE 2>&1 || {
    testfailed
}

if (( "$(fmbt-log weight.log | grep iFoo | wc -l)" < 3 )); then
    testfailed
fi
testpassed

teststep "heuristic weight: only one"
(cat test-noheur.conf; echo 'heuristic = "weight(test-onlyone.weight)"') > test-onlyone.conf
fmbt test-onlyone.conf -l weight.log >>$LOGFILE 2>&1 || {
    testfailed
}
if (( "$(fmbt-log weight.log | grep iFoo | wc -l)" != 100 )); then
    testfailed
fi
testpassed

teststep "heuristic weight: fifty fifty"
(cat test-noheur.conf; echo 'heuristic = "weight(test-fiftyfifty.weight)"') > test-fiftyfifty.conf
fmbt test-fiftyfifty.conf -l weight.log >>$LOGFILE 2>&1 || {
    testfailed
}
if (( "$(fmbt-log weight.log | grep iFoo | wc -l)" < 10 )); then
    echo "too few iFoos in the log" >> $LOGFILE
    testfailed
fi

if (( "$(fmbt-log weight.log | grep iBar | wc -l)" < 10 )); then
    echo "too few iBars in the log" >> $LOGFILE
    testfailed
fi
if (( "$(fmbt-log weight.log | grep iBar | wc -l)" + "$(fmbt-log weight.log | grep iFoo | wc -l)" != 100 )); then
    testfailed
fi
testpassed
