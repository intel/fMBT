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

# This tests fMBT with models that have deadlocks and "output only"
# states. Models have various number of input and output actions (from
# 0 to 2 of each). Different end conditions and test generation
# heuristics are tested.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.deadlocks.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

fmbt-gt -o model.lsts -f - <<EOF
P(choose-model, p) ->

T(choose-model,       "iModel('dead')",                additional-actions)
T(choose-model,       "iModel('dead-after-input')",    additional-actions)
T(choose-model,       "iModel('outonly')",             additional-actions)
T(choose-model,       "iModel('outonly-after-input')", additional-actions)

T(additional-actions, "iActions(i=0, o=0)",      choose-heuristic)
T(additional-actions, "iActions(i=1, o=0)",      choose-heuristic)
T(additional-actions, "iActions(i=0, o=1)",      choose-heuristic)
T(additional-actions, "iActions(i=1, o=1)",      choose-heuristic)

T(choose-heuristic,   "iHeur('lookahead')",      end-conditions)
T(choose-heuristic,   "iHeur('lookahead(5)')",    end-conditions)
T(choose-heuristic,   "iHeur('lookahead(5b)')",   end-conditions)
T(choose-heuristic,   "iHeur('random')",         end-conditions)

T(end-conditions,     "iEnd('deadlock')",        require-inconc)
T(end-conditions,     "iEnd(None)",              require-deadlock)

T(require-inconc,     "iRun('inconc')",          choose-model)
T(require-deadlock,   "iRun('deadlock')",        choose-model)
EOF

