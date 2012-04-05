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


cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.coverage.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

teststep "coverage: generate model"
fmbt-gt -f t1.gt -o t1.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed

teststep "Coverage perm"
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "perm:1"' >> test.conf

fmbt test.conf -l perm.log >>$LOGFILE 2>&1 || {
    testfailed
}

fmbt-log -f \$sc perm.log|head -1|while read f
do
if [ 0.000000 != $f ]; then
    testfailed
#    exit 1
fi
done

fmbt-log -f \$sc perm.log|tail -1|while read l
do
if [ 1.000000 != $l ]; then
    testfailed
#    exit 1
fi
done

testpassed

teststep "Coverage tag"
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "tag"' >> test.conf

fmbt test.conf -l tag.log >>$LOGFILE 2>&1 || {
    testfailed
#    exit 1    
}

fmbt-log -f \$sc tag.log|head -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
#    exit 1
fi
done

fmbt-log -f \$sc tag.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
#    exit 1
fi
done

testpassed

teststep "coverage: generate model2"
fmbt-gt -f t2.gt -o t2.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed


teststep "Coverage tag with model..."
echo 'model = "lsts:t2.lsts"' > test.conf
echo 'coverage = "tag"' >> test.conf

fmbt test.conf -l tag.log >>$LOGFILE 2>&1 || {
    testfailed
#    exit 1    
}

fmbt-log -f \$sc tag.log|head -1|while read f
do
if [ 0.000000 != $f ]; then
    testfailed
#    exit 1
fi
done

fmbt-log -f \$sc tag.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
#    exit 1
fi
done

testpassed
