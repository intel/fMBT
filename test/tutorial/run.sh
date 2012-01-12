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


# This test runs through the commands in the doc/tutorial.txt.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.tutorial.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

##########################################
# Run the test

teststep "extract fmbt commands from tutorial..."
rm -f create.* fmbt.* sed.* log.*
awk '/^\$ .*EOF/{p=1; k=1; $1=""; cn+=1; f="create."cn}
     /^\$ fmbt /{if (f) break; p=1; k=0; $1=""; rn+=1; f="fmbt."rn}
     /^\$ fmbt-log/{if (f) break; p=1; k=0; $1=""; ln+=1; f="log."ln}
     /^\$ sed/{if (f) break; p=1; k=0; $1=""; sn+=1; f="sed."sn}
     /^\$ echo/{if (f) break; p=1; k=0; $1=""; en+=1; f="echo."en}
     /^EOF$/{k=0}
     {if (p) print >> f;
      if (!k) { p=0; f=""} }' ../../doc/tutorial.txt
check_minimum_num_of_lines create.3 1
check_minimum_num_of_lines fmbt.3 1
testpassed

teststep "create the simple model (create.1)"
source create.1
check_minimum_num_of_lines mkrmdir.lsts 30
testpassed

teststep "create the configuration file (create.2)"
source create.2
check_minimum_num_of_lines mkrmdir.conf 5
testpassed

teststep "run:$(cat fmbt.1)..."
rm -rf /tmp/fmbt.mkrmdir
rm -f mkrmdir.log
source fmbt.1
if [ "$(fmbt-log -f '$tr' mkrmdir.log)" != "coverage reached" ]; then
    echo "coverage was not reached" >> $LOGFILE
    testfailed
fi
testpassed

teststep "modify the model..."
source create.3
check_minimum_num_of_lines mkrmdir.lsts 30
testpassed

teststep "modify perm and step limit in configuration..."
if grep -q steps: mkrmdir.conf || ! grep -q perm:1 mkrmdir.conf; then
    echo "steps does or perm:1 do not exist in original configuration" >> $LOGFILE
    testfailed
fi
source sed.1
source echo.1
if ! ( grep -q 100 mkrmdir.conf && grep -q perm:2 mkrmdir.conf ); then
    echo "steps:100 or perm:2 is missing in the configuration" >> $LOGFILE
    testfailed
fi
testpassed

teststep "rerun the test and check it fails now..."
rm -rf mkrmdir.log /tmp/fmbt.mkrmdir
echo q | source fmbt.3 >>$LOGFILE 2>&1
if [ $(fmbt-log -f '$tv' mkrmdir.log) != "fail" ]; then
    echo "test was passed unexpectedly" >> $LOGFILE
    testfailed
fi
testpassed

teststep "repeat the error trace (without minimising)..."
cp mkrmdir.log minimal.log
source log.6 2> errortrace.txt
if  ! ( grep adapter errortrace.txt | tail -n1 | grep NONE >> $LOGFILE 2>&1 ); then
    echo "adapter should not have responded on last step" >> $LOGFILE
    testfailed
fi
if ! ( grep adapter errortrace.txt | tail -n2 | head -n1 | grep -q 'File exists') ; then
    echo "expected last executed action to be mkdir existing dir" >> $LOGFILE
    testfailed
fi
testpassed
