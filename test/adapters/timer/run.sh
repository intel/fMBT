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

# Tests adapter_timer, test model defined in timer.gt

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.adapters.timer.log
MBTLOGFILE=/tmp/fmbt.test.adapters.timer.mbt.log
export PATH=../../../src:../../../utils:$PATH

source ../../functions.sh
rm -f $LOGFILE $MBTLOGFILE

##########################################
# Run the test

teststep "testing adapter_timer..."

fmbt -L$MBTLOGFILE timer.conf >>$LOGFILE 2>&1

VERDICT=$(fmbt-log -f '$tv' $MBTLOGFILE 2>>$LOGFILE)
REASON=$(fmbt-log -f '$tr' $MBTLOGFILE 2>>$LOGFILE)
if [ "$VERDICT" != "pass" ] ||
    [ "$REASON" != "step limit reached" ]; then
    echo "# Expected verdict: pass, reason: step limit reached." >> $LOGFILE
    echo "# Received verdict: $VERDICT, reason: $REASON" >> $LOGFILE
    testfailed
fi
testpassed
