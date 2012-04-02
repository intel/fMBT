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

# This tests fmbt-stats parameter combinations

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.fmbt-stats.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "generate log files..."
fmbt-gt -f model.gt -o model.lsts >>$LOGFILE 2>&1
cat > test.conf <<EOF
model = "lsts:model.lsts"
inconc = "steps:100000"
EOF
fmbt test.conf -l stats-input-100000.log >>$LOGFILE 2>&1
cat > test.conf <<EOF
model = "lsts:model.lsts"
inconc = "steps:100"
EOF
fmbt test.conf -l stats-input-100.log >>$LOGFILE 2>&1
cat > test.conf <<EOF
model = "lsts:model.lsts"
inconc = "steps:2"
EOF
fmbt test.conf -l stats-input-2.log >>$LOGFILE 2>&1
cat > test.conf <<EOF
model = "lsts:model.lsts"
inconc = "steps:1"
EOF
fmbt test.conf -l stats-input-1.log >>$LOGFILE 2>&1
cat > test.conf <<EOF
model = "lsts:model.lsts"
adapter = "remote_lsts:echo 'this wont work'"
inconc = "steps:0"
EOF
fmbt test.conf -l stats-input-0.log >>$LOGFILE 2>&1
testpassed

cat > test.conf <<EOF
model     = "lsts:model.lsts"
adapter   = "remote:remote_python -l adapter.log -c 'from teststeps import *'"
heuristic = "lookahead:4"
coverage  = "perm:1"
inconc    = "coverage:1.1"
pass      = "no_progress:6"
on_fail   = "exit:1"
EOF

teststep "fmbt-stats with many args..."
fmbt test.conf -l test.log >>$LOGFILE 2>&1 || {
    testfailed
    exit 1
}
testpassed
