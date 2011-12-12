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
LOGFILE=/tmp/fmbt.test.aal_tutorial.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

##########################################
# Run the test

teststep "extract fmbt commands from aal_tutorial..."
rm -f create.* fmbt.* sed.* log.*
awk '/^\$ .*EOF/{p=1; k=1; $1=""; cn+=1; f="create."cn}
     /^\$ fmbt /{if (f) break; p=1; k=0; $1=""; rn+=1; f="fmbt."rn}
     /^\$ fmbt-log/{if (f) break; p=1; k=0; $1=""; ln+=1; f="log."ln}
     /^\$ sed/{if (f) break; p=1; k=0; $1=""; sn+=1; f="sed."sn}
     /^EOF$/{k=0}
     {if (p) print >> f;
      if (!k) { p=0; f=""} }' ../../doc/aal_tutorial.txt

check_minimum_num_of_lines create.1 5
check_minimum_num_of_lines create.2 5
check_minimum_num_of_lines create.3 7
check_minimum_num_of_lines create.4 5
testpassed

teststep "create the simple adapter (create.1)"
source create.1
check_file_exists libmymkdirrmdir.so
testpassed

teststep "create the model (create.2)"
source create.2
check_minimum_num_of_lines mkrmdir.lsts 6
testpassed

teststep "create the configuration file (create.3)"
source create.3
check_minimum_num_of_lines mkrmdir_aal.conf 6
testpassed

teststep "create the mrules file (create.4)"
source create.4
check_minimum_num_of_lines mkrmdir_aal.conf 4
testpassed

teststep "run: $(cat fmbt.1)..."
rm -rf /tmp/fmbt.mkrmdir
rm -f mkrmdir_aal.log
LD_LIBRARY_PATH=`pwd` source fmbt.1

if [ "$(fmbt-log -f '$tr' mkrmdir_aal.log)" != "coverage reached" ]; then
    echo "coverage was not reached" >> $LOGFILE
    testfailed
fi
testpassed
