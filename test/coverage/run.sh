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

teststep "coverage: generate model..."
fmbt-gt -f t1.gt -o t1.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed

teststep "coverage perm..."
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

teststep "coverage min..."
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "min:perm:3:perm:2"' >> test.conf
echo 'model = "lsts:t1.lsts"' > test2.conf
echo 'coverage = "min:perm:2:perm:3"' >> test2.conf

fmbt test.conf -l min1.log >>$LOGFILE 2>&1 || {
    testfailed
}

fmbt test2.conf -l min2.log >>$LOGFILE 2>&1 || {
    testfailed
}

fmbt-log -f \$sc min1.log | tail -1 | while read c
do
    if [ 0.333333 != $c ]; then
	testfailed
    fi
done

fmbt-log -f \$sc min1.log > log1
fmbt-log -f \$sc min2.log > log2

#cmp log1 log2 || {
#    testfailed 
#}

testpassed

teststep "coverage tag..."
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

teststep "coverage: generate model2..."
fmbt-gt -f t2.gt -o t2.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1    
}
testpassed


teststep "coverage tag with model..."
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


teststep "coverage: walks between tags"
cat > walks.conf <<EOF
model     = "aal_remote(remote_pyaal -l twocounters.aal.log 'twocounters.aal')"
heuristic = "lookahead(5)"
coverage  = "walks(from \"all_zeros\" to \"all_ones\")"
pass      = "coverage(2)"
fail      = "steps(20)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt walks.conf 2>walks-verdict.txt | fmbt-log | tee walks-steps-seen.txt >>$LOGFILE

cat > walks-steps-required.txt <<EOF
iIncX
iIncY
iReset
iIncX
iIncY
pass
EOF

if diff -u walks-steps-required.txt walks-steps-seen.txt >>$LOGFILE; then
    testpassed
else
    ( testfailed )
fi

teststep "coverage: uwalks between tags..."
cat > uwalks.conf <<EOF
model     = "aal_remote(remote_pyaal -l twocounters.aal.log 'twocounters.aal')"
heuristic = "lookahead(5)"
coverage  = "uwalks(from \"all_zeros\" to \"all_ones\")"
pass      = "coverage(1)"
fail      = "steps(20)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt uwalks.conf 2>uwalks-verdict.txt | fmbt-log | tee uwalks-steps-seen.txt >>$LOGFILE

cat > uwalks-steps-required.txt <<EOF
iIncX
iIncY
pass
EOF

if diff -u uwalks-steps-required.txt uwalks-steps-seen.txt >>$LOGFILE;
then
    testpassed
else
    testfailed
fi

teststep "coverage: include"
cat > cinclude.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc.gt')"
heuristic = "lookahead(1)"
coverage  = "include(iA,perm(1))"
fail      = "steps(2)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt cinclude.conf -l cinclude.log 2> cinclude.txt || {
    testfailed
    exit 1
}

fmbt-log -f \$sc cinclude.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed

teststep "coverage: exclude"
cat > cexclude.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc.gt')"
heuristic = "lookahead(1)"
coverage  = "exclude(iA,perm(1))"
fail      = "steps(3)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt cexclude.conf -l cexclude.log 2> cexclude.txt || {
    testfailed
    exit 1
}

fmbt-log -f \$sc cexclude.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed
