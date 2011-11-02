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

# This test runs through the commands in the doc/adapters.txt

##########################################
# Setup test environment

TESTDIR=/tmp/fmbt.test.adapters

cd "$(dirname "$0")"
cd ../..
chmod -R u+w $TESTDIR >/dev/null 2>&1
rm -rf $TESTDIR >/dev/null 2>&1
mkdir $TESTDIR
cp -rp * $TESTDIR || {
    echo "test setup error: copying src to src-test.adapter failed"
    exit 1
}
cd $TESTDIR/src || {
    echo "test setup error: creating working directory $TESTDIR src failed"
    exit 2
}

LOGFILE=/tmp/fmbt.test.adapter.log
rm -f $LOGFILE
export PATH=.:$TESTDIR/utils:$PATH

source $TESTDIR/test/functions.sh

##########################################
# Run the test

teststep "extract commands from adapters.txt..."
rm -f cat.[0-9] sed.[0-9] log.[0-9] fmbt-gt.[0-9] fmbt.[0-9]
awk '/^\$ cat.*EOF/{p=1; k=1; $1=""; cn+=1; f="cat."cn}
     /^\$ sed/     {if (f) break; p=1; k=0; $1=""; sn+=1; f="sed."sn}
     /^\$ g\+\+ /  {if (f) break; p=1; k=0; $1=""; rn+=1; f="g++."rn}
     /^\$ make /   {if (f) break; p=1; k=0; $1=""; mn+=1; f="make."mn}
     /^\$ fmbt-gt /{if (f) break; p=1; k=0; $1=""; gn+=1; f="fmbt-gt."gn}
     /^\$.* fmbt / {if (f) break; p=1; k=0; $1=""; ln+=1; f="fmbt."ln}
     /^EOF$/{k=0}
     {if (p) print >> f;
      if (!k) { p=0; f=""} }' $TESTDIR/doc/adapters.txt
check_minimum_num_of_lines cat.3 1
check_minimum_num_of_lines sed.1 1
check_minimum_num_of_lines g++.1 1
check_minimum_num_of_lines fmbt-gt.1 1
check_minimum_num_of_lines fmbt.2 1
testpassed

teststep "creating mylocaladapter.cc (cat.1)..."
if [ -f "mylocaladapter.cc" ]; then
    echo "mylocaladapter.cc already exists"
    testfailed
fi
source cat.1
check_minimum_num_of_lines mylocaladapter.cc 20
testpassed

teststep "creating mysut.hh (cat.2)..."
source cat.2
check_minimum_num_of_lines mysut.hh 5
testpassed

teststep "creating plugin-test.conf (cat.3)..."
source cat.3
check_minimum_num_of_lines plugin-test.conf 5
testpassed

teststep "creating static-test.conf (cat.4)..."
source cat.4
check_minimum_num_of_lines static-test.conf 5
testpassed

teststep "creating test model mysut.lsts (fmbt-gt.1)..."
source fmbt-gt.1 >>$LOGFILE 2>&1
check_minimum_num_of_lines mysut.lsts 10
testpassed

teststep "building mylocaladapter into myadapters.so..."
source g++.1 >> $LOGFILE 2>&1
if [ ! -x myadapters.so ]; then
    echo "myadapters.so not found" >> $LOGFILE
    testfailed
fi
testpassed

if [ ! -x fmbt ]; then
    teststep "building fmbt..."
    make fmbt >> $LOGFILE 2>&1 || testfailed
    testpassed
fi

teststep "running fmbt with shared lib mylocaladapter..."
source fmbt.1 >> $LOGFILE 2>&1
if [ "$(fmbt-log -f '$tv' plugin.log)" != "pass" ]; then
    echo "test did not pass:" >> $LOGFILE
    fmbt-log plugin.log >> $LOGFILE
    testfailed
fi
testpassed

teststep "modifying LOCAL_ADAPTERS for static linking..."
source sed.1 >> $LOGFILE 2>&1
grep -q mylocaladapter.cc Makefile.am || testfailed
testpassed

teststep "rebuilding fmbt with new LOCAL_ADAPTERS..."
source make.1 >> $LOGFILE 2>&1 || testfailed
testpassed

teststep "running fmbt with static mylocaladapter..."
source fmbt.2 >> $LOGFILE 2>&1
if [ "$(fmbt-log -f '$tv' static.log)" != "pass" ]; then
    echo "test did not pass:" >> $LOGFILE
    fmbt-log static.log >> $LOGFILE
    testfailed
fi
testpassed

##########################################
# Clean up
cd /tmp
chmod -R u+w $TESTDIR
rm -rf $TESTDIR
