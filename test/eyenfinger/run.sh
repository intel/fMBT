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


# Tests for eyenfinger & eye4graphics

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.eyenfinger.log
rm -f $LOGFILE

if [ "$1" != "installed" ]; then
    export PATH=../../src:../../utils:$PATH
    export LD_LIBRARY_PATH=../../src/.libs:$LD_LIBRARY_PATH
    export PYTHONPATH=../../utils:$PYTHONPATH
fi

source ../functions.sh

##########################################
# Run the test

teststep "eyenfinger smoke test without OCR"
python -c '
from eyenfinger import *
iRead(source="screenshot2.png", ocr=False)
assert iVerifyIcon("screenshot2-icon.png")[1] == (6, 6, 27, 24), \
    "Failed to find screenshot2-icon.png from screenshot2.png"
' 2>&1 | tee -a $LOGFILE  | grep -q . && {
    testfailed
}
testpassed


teststep "eyenfinger states"
if fmbt -l test.log test.aal.conf 2>fmbt.output; then
    fmbt-log test.log >>$LOGFILE
    cat fmbt.output >>$LOGFILE
    testpassed
else
    cat test.log fmbt.output >>$LOGFILE
    testfailed
fi

teststep "eye4graphics: bitmap self-comparison"
( python -c '
import fmbtgti
ti=fmbtgti.GUITestInterface()
ti.refreshScreenshot("screenshot2-icon.png")
print ti.verifyBitmap("screenshot2-icon.png")' 2>&1 | grep -q True && {
    testpassed
} ) || testfailed

teststep "eye4graphics: too small screenshot"
( python -c '
import fmbtgti
ti=fmbtgti.GUITestInterface()
ti.refreshScreenshot("screenshot2-icon.png")
print ti.verifyBitmap("screenshot2.png")' 2>&1 | grep -q False && {
    testpassed
} ) || testpassed
