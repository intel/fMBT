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


# This test tests remote model and AAL/Python

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.remoteerror.log
rm -f $LOGFILE

if [ "$1" != "installed" ]; then
    export PATH=../../src:../../utils:$PATH
    export PYTHONPATH=../../utils
fi

source ../functions.sh

##########################################
# Run the test

teststep "remote aal errors..."
failure_count=0
for WHEN in "load" "init" "iguard" "iadapter" "ibody" "oguard" "oadapter" "obody"; do
    for WHAT in "raise" "crash" "stdout" "stderr"; do
        for HEURISTIC in "random" "lookahead(2)"; do
            echo "" >> $LOGFILE
            echo "AAL, heur=$HEURISTIC, when: $WHEN  problem: $WHAT" >> $LOGFILE

            cat > test.conf <<EOF
model     = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"$WHEN-$WHAT\"' crashraise.aal)"
adapter   = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"$WHEN-$WHAT\"' crashraise.aal)"
heuristic = "$HEURISTIC"
pass      = "steps(3)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
on_error  = "exit(84)"
EOF
            echo "---- begin of test.conf ----" >>$LOGFILE
            cat test.conf >>$LOGFILE
            echo "---- end of test.conf ----" >>$LOGFILE

            echo "---- begin of fmbt log ----" >>$LOGFILE
            fmbt test.conf >>$LOGFILE 2>fmbt-output.txt
            FMBTSTATUS=$?
            echo "---- end of fmbt log ----" >>$LOGFILE

            echo "---- begin of fmbt-output.txt ----" >>$LOGFILE
            cat fmbt-output.txt >>$LOGFILE
            echo "---- end of fmbt-output.txt ----" >>$LOGFILE

            if [ "$FMBTSTATUS" != "84" ]; then
                echo "fails because: exit status $FMBTSTATUS, expected 84" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi

            if [ "$WHAT" == "crash" ] && ! grep -q 'Segmentation' fmbt-output.txt; then
                echo "fails because: segmentation fault missing in fmbt-output.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            elif [ "$WHAT" == "raise" ] && ! grep -q 'BogusException' fmbt-output.txt; then
                echo "fails because: raised exception missing in fmbt-output.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            elif ( [ "$WHAT" == "stderr" ] || [ "$WHAT" == "stdout" ] ) && ! grep -q 'rubbishFromAAL' fmbt-output.txt; then
                echo "fails because: rubbish printed from AAL is missing in fmbt-output.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
        done
    done
done

if [[ "$failure_count" != "0" ]]; then
    echo "failed combinations in total: $failure_count" >>$LOGFILE
    ( testfailed )
else
    testpassed
fi


teststep "remote adapter errors..."
failure_count=0
for WHEN in "load" "input"; do
    for WHAT in "raise" "crash" "stdout" "stderr"; do

        echo "" >> $LOGFILE
        echo "remote adapter, when: $WHEN  problem: $WHAT" >> $LOGFILE

        cat > test.conf <<EOF
model     = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"none-none\"' crashraise.aal)"
adapter   = "remote(remote_python -l remote_python.log -c 'BUG=\"$WHEN-$WHAT\"' -c 'from crashingsteps import *')"
heuristic = "random"
pass      = "steps(3)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
on_error  = "exit(84)"
EOF

        echo "---- begin of test.conf ----" >>$LOGFILE
        cat test.conf >>$LOGFILE
        echo "---- end of test.conf ----" >>$LOGFILE

        echo "---- begin of fmbt log ----" >>$LOGFILE
        fmbt test.conf >>$LOGFILE 2>fmbt-output.txt
        FMBTSTATUS=$?
        echo "---- end of fmbt log ----" >>$LOGFILE

        echo "---- begin of fmbt-output.txt ----" >>$LOGFILE
        cat fmbt-output.txt >>$LOGFILE
        echo "---- end of fmbt-output.txt ----" >>$LOGFILE

        if [ "$FMBTSTATUS" != "84" ]; then
            echo "fails because: exit status $FMBTSTATUS, expected 84" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        fi
        if [ "$WHAT" == "crash" ] && ! grep -q 'Segmentation' fmbt-output.txt; then
            echo "fails because: segmentation fault missing in fmbt-output.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "raise" ] && ! grep -q 'BogusException' fmbt-output.txt; then
            echo "fails because: raised exception missing in fmbt-output.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "stdout" ] && ! grep -q 'rubbish-to-stdout' fmbt-output.txt; then
            echo "fails because: rubbish-to-stdout from crashingsteps.py is missing in fmbt-output.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "stderr" ] && ! grep -q 'rubbish-to-stderr' fmbt-output.txt; then
            echo "fails because: rubbish-to-stderr from crashingsteps.py is missing in fmbt-output.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        fi
    done
done

if [[ "$failure_count" != "0" ]]; then
    echo "failed combinations in total: $failure_count" >>$LOGFILE
    ( testfailed )
else
    testpassed
fi
