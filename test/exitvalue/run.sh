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

# This tests fMBT with models that have deadlocks and "output only"
# states. Models have various number of input and output actions (from
# 0 to 2 of each). Different end conditions and test generation
# heuristics are tested.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.exitvalue.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "exitvalue on failure"

fmbt-gt -o model.lsts -f - <<EOF
P(first, p) ->
T(first,       "i1",                a1)
T(first,       "i2",                a2)
EOF

cat > test.conf<<EOF
model="lts:model.lsts"
adapter="dummy:1"
on_fail   = "exit:1"
on_pass   = "exit:2"
EOF

fmbt test.conf  >>$LOGFILE 2>&1
if [ $? -ne 1 ] 
then
    testfailed
else
    testpassed
fi

teststep "exitvalue on inconclusive deadlock"

cat > test.conf<<EOF
model="lts:model.lsts"
adapter="dummy"
inconc="deadlock"
on_fail   = "exit:1"
on_pass   = "exit:2"
on_inconc = "exit:3"
EOF

fmbt test.conf  >>$LOGFILE 2>&1
if [ $? -ne 3 ]
then
    testfailed
else
    testpassed
fi

teststep "exitvalue on passed"

cat > test.conf<<EOF
model="lts:model.lsts"
adapter="dummy"
on_fail   = "exit:1"
on_pass   = "exit:2"
on_inconc = "exit:3"
EOF

fmbt test.conf  >>$LOGFILE 2>&1
if [ $? -ne 2 ]
then
    testfailed
else
    testpassed
fi


teststep "exitvalue on error (input action)"

cat > test.conf<<EOF
model="lts:model.lsts"
adapter="dummy:2"
on_fail   = "exit:1"
on_pass   = "exit:2"
on_inconc = "exit:3"
on_error  = "exit:4"
EOF

fmbt test.conf  >>$LOGFILE 2>&1
if [ $? -ne 4 ]
then
    testfailed
else
    testpassed
fi

teststep "exitvalue on error (output: communication error)"

cat > test.conf<<EOF
model="lts:model.lsts"
adapter="dummy:2:1"
on_fail   = "exit:1"
on_pass   = "exit:2"
on_inconc = "exit:3"
on_error  = "exit:4"
EOF

fmbt-gt --keep-labels -o model.lsts -f - <<EOF
P(first, p) ->
T(first,       "o1",                a1)
EOF

fmbt test.conf  >>$LOGFILE 2>&1
if [ $? -ne 4 ]
then
    testfailed
else
    testpassed
fi
