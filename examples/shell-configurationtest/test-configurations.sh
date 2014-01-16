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

##########################################
# This script demonstrates configuration testing: test all
# combinations of configurations.
#
# Test model states:
#
# prepare_source -> build_n_install -> test* -> cleanup
#     ^                                            |
#     |                                            |
#     +--------------------------------------------+
#
# *) run a test set suitable for the installed
#    target

fmbt-gt -o testmodel.lsts -f - <<EOF
P(prepare_source,  "gt:istate") ->
P(prepare_source,  "gt:istate")

T(prepare_source,  "iSourceTarGz",       build_n_install)
T(prepare_source,  "iSourceGitClone",    build_n_install)

T(build_n_install, "iMakeInstFmbt",      test_fmbt)
T(build_n_install, "iMakeInstDroid",     test_fmbtdroid)
T(build_n_install, "iAndroidBuild",      test_android)
T(build_n_install, "iBuildInstDebPkg",   test_fmbt)
T(build_n_install, "iBuildInstRPMPkg",   test_fmbt)

T(test_fmbt,       "iTestFmbt",          cleanup)
T(test_fmbtdroid,  "iTestFmbtDroid",     cleanup)
T(test_android,    "iTestOnAndroid",     cleanup)

T(cleanup,         "iCleanup",           prepare_source)
EOF

##########################################
# Test steps. These shell functions will be called when the test is
# executed. For this example they only print what would be done.

iSourceTarGz() {
    echo -n "use fmbt.tar.gz...     "
}

iSourceGitClone() {
    echo -n "use git clone...       "
}

iMakeInstFmbt() {
    echo -n "make install...        "
}

iMakeInstDroid() {
    echo -n "make fmbt_droid...     "
}

iAndroidBuild() {
    echo -n "ndk-build...           "
}

iBuildInstDebPkg() {
    echo -n "dpkg-buildpackage...   "
}

iBuildInstRPMPkg() {
    echo -n "rpmbuild...            "
}

iTestFmbt() {
    echo -n "  - test fmbt...       "
}

iTestFmbtDroid() {
    echo -n "  - test fmbt_droid... "
}

iTestOnAndroid() {
    echo -n "  - test on android... "
}

iCleanup() {
    echo -n "  - cleanup...         "
}

##########################################
# Test configuration.

# As we want to test every combination of 1) source and 2) target, and
# there's no 3rd configuration parameter, perm:2 covers all of them.
# no_progress end condition will top test generation after 4 generated
# steps without covering any new configurations.

cat > test.conf <<EOF
model     = "testmodel.lsts"
coverage  = "perm(2)"
heuristic = "lookahead(4)"
pass      = "no_progress:4"
# disable built-in coverage end condition:
fail      = "coverage:1.1"
fail      = "steps:100"
on_fail   = "exit"
EOF

##########################################
# Generate and run the test.

# This is an "offline" test: test.conf does not define an
# adapter. fmbt only generates and simulates the test run. Yet nothing
# is actually executed, simulated test steps are logged.
#
# We use fmbt-log to pick up the generated test from the log. Then we
# call the corresponding test step (shell function) for each step:

fmbt test.conf | fmbt-log -f '$as' | while read teststep; do

    if eval "$teststep"; then
        echo "pass"
    else
        echo "fail"
    fi

done
