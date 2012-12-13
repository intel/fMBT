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
for WHEN in "load" "init" "iguard" "iadapter" "ibody" "oguard" "oadapter" "obody" "tguard"; do
    for WHAT in "raise" "crash" "stdout" "stderr"; do

        # remote protocols handle the first stdout printing
        # as part of action list. fixing this needs changing
        # the protocol to recognise fmbt printing from other
        # output. before that is fixed, we'll skip this test.
        if [ "$WHEN-$WHAT" == "load-stdout" ]; then continue; fi

        for HEURISTIC in "random" "lookahead(2)"; do
            echo "" >> $LOGFILE
            echo "AAL, heur=$HEURISTIC, when: $WHEN  problem: $WHAT" >> $LOGFILE

            cat > test.$WHEN.$WHAT.$HEURISTIC.aal.conf <<EOF
model     = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"$WHEN-$WHAT\"' crashraise.aal)"
adapter   = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"$WHEN-$WHAT\"' crashraise.aal)"
heuristic = "$HEURISTIC"
pass      = "steps(3)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
on_error  = "exit(84)"
EOF
            echo "---- begin of test.$WHEN.$WHAT.$HEURISTIC.aal.conf ----" >>$LOGFILE
            cat test.$WHEN.$WHAT.$HEURISTIC.aal.conf >>$LOGFILE
            echo "---- end of test.$WHEN.$WHAT.$HEURISTIC.aal.conf ----" >>$LOGFILE

            echo "---- begin of fmbt log ----" >>$LOGFILE
            fmbt test.$WHEN.$WHAT.$HEURISTIC.aal.conf >>$LOGFILE 2>fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt
            FMBTSTATUS=$?
            echo "---- end of fmbt log ----" >>$LOGFILE

            echo "---- begin of fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt ----" >>$LOGFILE
            cat fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt >>$LOGFILE
            echo "---- end of fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt ----" >>$LOGFILE

            if [ "$WHAT" != "stderr" ] && [ "$FMBTSTATUS" != "84" ]; then
                echo "fails because: exit status $FMBTSTATUS, expected 84" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if [ "$WHAT" == "stderr" ] && [ "$FMBTSTATUS" != "0" ]; then
                echo "fails because: exit status $FMBTSTATUS, expected 0" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if [ "$WHAT" == "crash" ] && ! grep -q 'Terminated by a signal (11)' fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt; then
                echo "fails because: segmentation fault missing in fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if [ "$WHAT" == "raise" ] && ! grep -q 'BogusException' fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt; then
                echo "fails because: raised exception missing in fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if [ "$WHAT" == "raise" ] && ! grep -q 'check_bug' fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt; then
                echo "fails because: check_bug function call missing AAL/Python traceback in fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if [ "$WHAT" == "raise" ] && ! grep -q 'raise Exception("BogusException' fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt; then
                echo "fails because: raise Exception(...) call missing AAL/Python traceback in fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt" >>$LOGFILE
                failure_count=$(( $failure_count + 1 ))
            fi
            if ( [ "$WHAT" == "stderr" ] || [ "$WHAT" == "stdout" ] ) && ! grep -q 'rubbishFromAAL' fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt; then
                echo "fails because: rubbish printed from AAL is missing in fmbt-output.$WHEN.$WHAT.$HEURISTIC.aal.txt" >>$LOGFILE
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

        cat > test.$WHEN.$WHAT.remote.conf <<EOF
model     = "aal_remote(remote_pyaal -l aal.log -c 'BUG=\"none-none\"' crashraise.aal)"
adapter   = "remote(remote_python -l remote_python.log -c 'BUG=\"$WHEN-$WHAT\"' -c 'from crashingsteps import *')"
heuristic = "random"
pass      = "steps(3)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
on_error  = "exit(84)"
EOF

        echo "---- begin of test.$WHEN.$WHAT.remote.conf ----" >>$LOGFILE
        cat test.$WHEN.$WHAT.remote.conf >>$LOGFILE
        echo "---- end of test.$WHEN.$WHAT.remote.conf ----" >>$LOGFILE

        echo "---- begin of fmbt log ----" >>$LOGFILE
        fmbt test.$WHEN.$WHAT.remote.conf >>$LOGFILE 2>fmbt-output.$WHEN.$WHAT.remote.txt
        FMBTSTATUS=$?
        echo "---- end of fmbt log ----" >>$LOGFILE

        echo "---- begin of fmbt-output.$WHEN.$WHAT.remote.txt ----" >>$LOGFILE
        cat fmbt-output.$WHEN.$WHAT.remote.txt >>$LOGFILE
        echo "---- end of fmbt-output.$WHEN.$WHAT.remote.txt ----" >>$LOGFILE

        if [ "$WHEN-$WHAT" == "input-raise" ] && [ "$FMBTSTATUS" != "1" ]; then
            echo "fails because: exit status $FMBTSTATUS, expected 1" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        fi
        if [ "$WHEN-$WHAT" != "input-raise" ] && [ "$FMBTSTATUS" != "84" ]; then
            echo "fails because: exit status $FMBTSTATUS, expected 84" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        fi
        if [ "$WHAT" == "crash" ] && ! ( grep -q 'Terminated by a signal (11)' fmbt-output.$WHEN.$WHAT.remote.txt || \
                                         grep -q 'communication failure' fmbt-output.$WHEN.$WHAT.remote.txt ); then
            echo "fails because: segmentation fault missing in fmbt-output.$WHEN.$WHAT.remote.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "raise" ] && ! grep -q 'BogusException' fmbt-output.$WHEN.$WHAT.remote.txt; then
            echo "fails because: raised exception missing in fmbt-output.$WHEN.$WHAT.remote.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "stdout" ] && ! grep -q 'rubbish-to-stdout' fmbt-output.$WHEN.$WHAT.remote.txt; then
            echo "fails because: rubbish-to-stdout from crashingsteps.py is missing in fmbt-output.$WHEN.$WHAT.remote.txt" >>$LOGFILE
            failure_count=$(( $failure_count + 1 ))
        elif [ "$WHAT" == "stderr" ] && ! grep -q 'rubbish-to-stderr' fmbt-output.$WHEN.$WHAT.remote.txt; then
            echo "fails because: rubbish-to-stderr from crashingsteps.py is missing in fmbt-output.$WHEN.$WHAT.remote.txt" >>$LOGFILE
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
