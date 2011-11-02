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

# This script tests the last commit in the current branch of git.

LOGFILE=/tmp/fmbt.test.git-HEAD.txt

TESTDIR=/tmp/fmbt.test.git-HEAD

BRANCH=$(git branch | awk '/\*/{print $2}')

rm -rf $TESTDIR
mkdir -p $TESTDIR

( git archive $BRANCH | tar xvf - -C $TESTDIR ) >>$LOGFILE 2>&1 || {
    echo "Running \"git archive $BRANCH\" failed, see $LOGFILE"
    exit 1
}

cd $TESTDIR

test/build/run.sh || exit 1

for f in test/*/run.sh; do
    dirname=$(echo $f | sed 's:.*/\(.*\)/.*$:\1:')
    if [ $dirname == "git-HEAD" ] || [ $dirname == "build" ]; then
	continue; # skip these tests
    fi
    $f
done
