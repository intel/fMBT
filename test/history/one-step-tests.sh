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

# This skript tests "history" configuration by generating one-step
# tests according to one-step-tests.conf. If there are more than three
# of them, something is wrong.

rm -f test?.log

verdict="inconclusive"
testnumber=0

while [ "$verdict" == "inconclusive" ]; do

    if [ $testnumber -gt 3 ]; then
        echo "Too many tests: $testnumber. Should have passed already."
        exit 1
    fi

    # Configuration for the next test run (next-test.conf) is built as
    # follows:
    # 
    # - one-step-tests.conf is used as starting point
    #
    # - for each previous test NUM, one line is appended to the
    #   configuration for each previous test X:
    #
    #   history = "log:test<NUM>.log"

    cp one-step-tests.conf next-test.conf

    for prev_test in $(seq 1 $testnumber); do
        echo "history = \"log:test$prev_test.log\"" >> next-test.conf
    done

    testnumber=$(( $testnumber + 1 ))

    # Run the test

    fmbt -l test$testnumber.log next-test.conf

    verdict=$(fmbt-log -f '$tv' test$testnumber.log)
done

if [ "$verdict" != "pass" ]; then
    echo "Unexpected verdict after $testnumber tests: $verdict"
    exit 2
fi

if [ "$testnumber" != "3" ]; then
    echo "Unexpected number of tests before pass: $testnumber"
    exit 3
fi

all_steps=$(echo $(fmbt-log -f '$ax' test?.log | sort))

if [ "$all_steps" != "iA iB iC" ]; then
    echo "Unexpected steps executed: $all_steps"
    exit 4
fi

# Everything is fine on this line. Successful exit.
