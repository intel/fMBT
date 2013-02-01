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
LOGFILE=/tmp/fmbt.test.reporting.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "reporting: generate pause/continue test..."

cat > reliability.conf <<EOF
model     = "aal_remote(remote_pyaal -l mplayertest.aal.log 'mplayertest.aal')"
heuristic = "lookahead(3)"
coverage  = "sum(uinputs(from 'iContinue' to 'iPause'),
                 uinputs(from 'iPause' to 'iContinue'))"
pass      = "coverage(40)"
fail      = "steps(150)"
fail      = "noprogress(3)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

if ! fmbt -l reliability.log reliability.conf >> $LOGFILE 2>&1; then
    testfailed
fi
testpassed


teststep "reporting: fmbt-ucheck..."
cat > report_cases.uc <<EOF
report "do things while PLAYING" from 'iContinue' to 'iPause'
report "do things when PAUSED" from 'iPause' to 'iContinue'
report "USECASE-PAUCON" "usecase('iPau.*' then 'iCon.*')"
report "USECASE-CONPAU" "usecase('iCon.*' then 'iPau.*')"
EOF

if ! fmbt-ucheck -f html -u report_cases.uc -o report.html reliability.log >> $LOGFILE 2>&1; then
    echo "unexpected exitstatus $? from fmbt-ucheck -f html..." >>$LOGFILE
    testfailed
fi
if ! fmbt-ucheck -f csv -u report_cases.uc -o report.csv reliability.log >> $LOGFILE 2>&1; then
    echo "unexpected exitstatus $? from fmbt-ucheck -f csv..." >>$LOGFILE
    testfailed
fi
if ! grep PLAYING report.html | grep 20 >> $LOGFILE 2>&1; then
    echo "checking 20 PLAYING reports in html failed" >>$LOGFILE
    testfailed
fi
if ! grep PAUSED report.html | grep 20 >> $LOGFILE 2>&1; then
    echo "checking 20 PAUSED reports in html failed" >>$LOGFILE
    testfailed
fi

# BUG: from iContinue to iPause html report does not report the last
# step in CSV.
#
# if ! [ "$(grep PLAYING report.csv | wc -l)" == "20" ]; then
#     grep PLAYING report.csv | nl >>$LOGFILE
#     echo "checking 20 PLAYING reports in csv failed" >>$LOGFILE
#     testfailed
# fi

if ! [ "$(grep PAUSED report.csv | wc -l)" == "20" ]; then
    grep PAUSED report.csv | nl >>$LOGFILE
    echo "checking 20 PAUSED reports in csv failed" >>$LOGFILE
    testfailed
fi
if ! [ "$(grep USECASE-PAUCON report.csv | wc -l)" == "20" ]; then
    grep USECASE-PAUCON report.csv | nl >> $LOGFILE
    echo "checking 20 USECASE-PAUCON reports in csv failed" >>$LOGFILE
    testfailed
fi
if ! [ "$(grep USECASE-CONPAU report.csv | wc -l)" == "20" ]; then
    grep USECASE-CONPAU report.csv | nl >> $LOGFILE
    echo "checking 20 USECASE-CONPAU reports in csv failed" >>$LOGFILE
    testfailed
fi
testpassed

