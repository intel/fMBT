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

# This tests fMBT building and installing in different configurations

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.all-builds.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

# Test model for building:
# 1. setup sources from which to build fMBT
# 2. build and install a target (fmbt, fmbt-droid, deb package, RPM package)
# 3. test installed target
# 4. clean-up and repeat from the start

fmbt-gt -o model.lsts -f - <<EOF
P(sources,    "gt:istate") ->
P(sources,    "gt:istate")
T(sources,    "iBuildFromSourceTarBall",  target)
T(sources,    "iBuildFromGitHead",        target)

T(target,     "iBuildFmbt",               testnormal)
T(target,     "iBuildFmbtDroid",          testdroid)
T(target,     "iBuildDebPackage",         testnormal)
T(target,     "iBuildRPMPackage",         testnormal)

T(testnormal, "iTestFmbt",                cleanup)

T(testdroid,  "iTestFmbtDroid",           cleanup)

T(cleanup,    "iCleanup",                 sources)
EOF

cat > test.conf <<EOF
model = "model.lsts"
coverage = "perm:2"
heuristic = "lookahead:2"
pass = "no_progress:6"
fail = "steps:100"
on_fail = "exit"
EOF

iBuildFromSourceTarBall() {
    echo "building from .tar.gz"
}

iBuildFromGitHead() {
    echo "building from git head"
}

iBuildFmbt() {
    echo "make fmbt"
}

iBuildFmbtDroid() {
    echo "building fmbtdroid"
}

iBuildDebPackage() {
    echo "building deb"
}

iBuildRPMPackage() {
    echo "building rpm"
}

iTestFmbt() {
    echo "test fmbt"
}

iTestFmbtDroid() {
    echo "test fmbt-droid"
}

iCleanup() {
    echo "rm build and installation"
}

fmbt test.conf | fmbt-log -f '$as' | while read teststep; do
    $teststep
done
