#!/bin/bash

# fMBT, free Model Based Testing tool
# Copyright (c) 2012, 2013 Intel Corporation.
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

teststep "coverage generate model..."
fmbt-gt -f t1.gt -o t1.lsts >>$LOGFILE 2>&1 || {
    testfailed
    exit 1
}
testpassed

teststep "coverage perm..."
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "perm:1"' >> test.conf

fmbt test.conf -l perm.log >>$LOGFILE 2>&1 || {
    echo "failed because exit status 0 expected" >>$LOGFILE
    testfailed
}

fmbt-log -f \$sb perm.log|head -1|while read f
do
if [ 0.000000 != $f ]; then
    echo "failed because initial coverage 0.000000 expected" >>$LOGFILE
    testfailed
fi
done

fmbt-log -f \$sc perm.log|tail -1|while read l
do
if [ 1.000000 != $l ]; then
    echo "failed because final coverage 1.000000 expected" >>$LOGFILE
    testfailed
fi
done
testpassed

teststep "coverage min..."
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "min(perm(3), perm(2),
                      perm(1))"' >> test.conf
echo 'model = "lsts:t1.lsts"' > test2.conf
echo 'coverage = "min(perm:1,perm:2,perm:3)"' >> test2.conf

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

cmp log1 log2 || {
    testfailed
}

testpassed

teststep "coverage tag..."
echo 'model = "lsts:t1.lsts"' > test.conf
echo 'coverage = "tag"' >> test.conf

fmbt test.conf -l tag.log >>$LOGFILE 2>&1 || {
    testfailed
}

fmbt-log -f \$sc tag.log|head -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
fi
done

fmbt-log -f \$sc tag.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
fi
done
testpassed

teststep "coverage tag with model 2..."
cat > test.conf <<EOF
model = "lsts_remote(fmbt-gt -f t2.gt)"
coverage = "tag"
pass = "coverage(1.0)"
on_fail = "exit(1)"
EOF

fmbt test.conf -l tag2.log >>$LOGFILE 2>&1 || {
    testfailed
}

if ! ( fmbt-log -f '$ax' tag2.log | grep -q iCoverSecond ); then
    echo "iCoverSecond should have been executed before reaching full coverage" >>$LOGFILE
    testfailed
fi
if fmbt-log -f '$ax' tag2.log | grep -q iCoverBoth; then
    echo "iCoverBoth should not have been executed - full coverage reached before it" >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage tag regexp case..."
cat > test.conf <<EOF
model = "lsts_remote(fmbt-gt -f t3.gt)"
coverage = tag("tag.*")
pass = "coverage(1.0)"
on_fail = "exit(1)"
EOF

fmbt test.conf -l tag2.log >>$LOGFILE 2>&1 || {
    testfailed
}

if ! ( fmbt-log -f '$ax' tag2.log | grep -q iCoverSecond ); then
    echo "iCoverSecond should have been executed before reaching full coverage" >>$LOGFILE
    testfailed
fi
if fmbt-log -f '$ax' tag2.log | grep -q iCoverBoth; then
    echo "iCoverBoth should not have been executed - full coverage reached before it" >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage walks between tags"
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

teststep "coverage uwalks between tags..."
cat > uwalks.conf <<EOF
model     = "aal_remote(remote_pyaal -l twocounters.aal.log 'twocounters.aal')"
heuristic = "lookahead(5)"
coverage  = "uwalks(from 'all_zeros' to 'all_ones')"
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

teststep "coverage uwalks between actions..."
cat > uwalks.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(7)"
coverage  = "uwalks(from 'iOrderCoffee' to 'iCollectItem')"
pass      = "coverage(5)"
fail      = "no_progress(10)"
fail      = "steps(100)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

if ! fmbt -l uwalks.log uwalks.conf 2>uwalks-verdict.txt; then
    echo "this uwalks.conf test was expected to pass:" >>$LOGFILE
    cat uwalks.conf >>$LOGFILE
    tail -n 20 uwalks.log >>$LOGFILE
    testfailed
fi

fmbt-log uwalks.log | tee uwalks-steps-seen.txt >>$LOGFILE

if [ "$(grep iCollectItem uwalks-steps-seen.txt | wc -l)" != "5" ]; then
    echo "five iCollectItem steps expected," >>$LOGFILE
    echo "$(grep iCollectItem uwalks-steps-seen.txt | wc -l) seen." >>$LOGFILE
    testfailed
fi

if grep -q iCancelOrder uwalks-steps-seen.txt; then
    echo "iCancelOrder appears in the log but it should not." >>$LOGFILE
    echo "- it does not add minimal unique walks" >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage usecase..."
cat > usecase.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'coffee.gt')"
heuristic = "lookahead(5)"
coverage  = "usecase(all 'iChoose.*' then ('iCh.*Cash' and 'iCh.*Credit'))"
pass      = "coverage(1.0)"
inconc    = "steps(20)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
if ! fmbt -l usecase.log usecase.conf 2>usecase-verdict.txt; then
    cat usecase.conf >>$LOGFILE
    tail -n 20 usecase.log >>$LOGFILE
    echo "failed because fmbt usecase.conf was expected to pass." >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log usecase.log | grep iChooseCash | wc -l)" != "2" ] ||
   [ "$(fmbt-log usecase.log | grep iChooseCredit | wc -l)" != "2" ]; then
    cat usecase.conf >>$LOGFILE
    tail -n 20 usecase.log >>$LOGFILE
    echo "failed because exactly two iChooseCash and iChooseCredit actions expected." >>$LOGFILE
    testfailed
fi
cat > usecase.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'coffee.gt')"
heuristic = "lookahead(5)"
coverage  = "usecase((not 'iCancelPayment' and 'iChooseCash' and 'iChooseCredit') then 'iCancelOrder')"
pass      = "coverage(1.0)"
inconc    = "steps(20)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
if ! fmbt -l usecase.log usecase.conf 2>usecase-verdict.txt; then
    cat usecase.conf >>$LOGFILE
    tail -n 20 usecase.log >>$LOGFILE
    echo "failed because fmbt usecase.conf was expected to pass." >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log usecase.log | grep iChooseCash | wc -l)" != "1" ] ||
   [ "$(fmbt-log usecase.log | grep iChooseCredit | wc -l)" != "1" ] ||
   [ "$(fmbt-log usecase.log | grep iCancelPayment | wc -l)" != "1" ] ||
   [ "$(fmbt-log usecase.log | grep iCancelOrder | wc -l)" != "1" ] ; then
    cat usecase.conf >>$LOGFILE
    tail -n 20 usecase.log >>$LOGFILE
    echo "failed because exactly one of iChooseCash, iChooseCredit, iCancelPayment and iCancelOrder expected." >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage usecase, multiply..."
cat > usecase-multiply.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'coffee.gt')"
heuristic = "lookahead(5)"
coverage  = "usecase(3 * (all 'iChoose.*') then 0 * 'i.*' then 2 * ('iOrder.*' or 'iCancelOrder') * 2)"
pass      = "coverage(1.0)"
inconc    = "steps(20)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
if ! fmbt -l usecase-multiply.log usecase-multiply.conf 2>usecase-multiply-verdict.txt; then
    cat usecase-multiply.conf >>$LOGFILE
    tail -n 20 usecase-multiply.log >>$LOGFILE
    echo "failed because fmbt usecase-multiply.conf was expected to pass." >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log usecase-multiply.log | grep iChooseCash | wc -l)" != "3" ] ||
   [ "$(fmbt-log usecase-multiply.log | grep iChooseCredit | wc -l)" != "3" ]; then
    cat usecase-multiply.conf >>$LOGFILE
    tail -n 20 usecase-multiply.log >>$LOGFILE
    echo "failed because exactly three iChooseCash and iChooseCredit actions expected." >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log -f '$ax' usecase-multiply.log | tail -n 4 | grep iOrderCoffee | wc -l)" != "2" ] ||
   [ "$(fmbt-log -f '$as' usecase-multiply.log | tail -n 4 | grep iCancelOrder | wc -l)" != "2" ]; then
    cat usecase-multiply.conf >>$LOGFILE
    tail -n 20 usecase-multiply.log >>$LOGFILE
    echo "failed because usecase-multiply.log should have ended with iCancelOrder, iOrderCoffee, iCancelOrder, iOrderCoffee." >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log -f '$ax' usecase-multiply.log | wc -l)" != "17" ]; then
    echo "failed because usecase-multiply contains too many steps. 17 is the optimal." >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage usecase, start-end-tags..."

cat > usecase-tags.conf.in <<EOF
model     = aal_remote(remote_pyaal -l usecase-tags.aal.log usecase-tags.aal)
adapter   = aal
heuristic = lookahead(6)

inconc    = steps(9)
pass      = coverage(1.0)
on_pass   = exit(0)
on_fail   = exit(1)
on_inconc = exit(2)
EOF
# test stopping each played sound when all sounds are playing
(cat usecase-tags.conf.in; echo 'coverage=usecase(@[all "hear.*"](all "i:stop.*"))') > usecase-tags.conf
if ! fmbt -l usecase-tags.log usecase-tags.conf >>$LOGFILE 2>&1; then
    cat usecase-tags.log >> $LOGFILE
    cat usecase-tags.conf >> $LOGFILE
    echo "failed because fmbt -l usecase-tags.conf returned non-zero exit status" >> $LOGFILE
    testfailed
fi
# check that when ever "i:stop ..." is executed, all tags were on
for stop_thing in i:stop-alert i:stop-game i:stop-music; do
    if ! ( fmbt-log -f '$ax\nTAGS: $tg' < usecase-tags.log | grep -B 1 $stop_thing | head -n 1 | grep hear-alert | grep hear-music | grep -q hear-game ); then
        cat usecase-tags.log >> $LOGFILE
        cat usecase-tags.conf >> $LOGFILE
        echo "failed because alert, game or music was not heard when executing $stop_thing" >> $LOGFILE
        testfailed
    fi
done
# test "exactly every 2" syntax
(cat usecase-tags.conf.in; echo 'coverage = usecase( [ exactly every 2 "hear-.*" ] ("i:stop-.*") )') > usecase-tags-exactly.conf
if ! fmbt -l usecase-tags-exactly.log usecase-tags-exactly.conf >>$LOGFILE 2>&1; then
    cat usecase-tags-exactly.log >> $LOGFILE
    cat usecase-tags-exactly.conf >> $LOGFILE
    echo "failed because fmbt -l usecase-tags-exactly.conf returned non-zero exit status" >> $LOGFILE
    testfailed
fi
# check that before each "i:stop ..." there was always unique
# combination of two tags
if [ $(fmbt-log -f '$ax\nTAGS: $tg' < usecase-tags-exactly.log | grep -B 1 i:stop- | grep TAGS | sort -u | wc -l) != "3" ]; then
    fmbt-log -f '$ax\nTAGS: $tg' < usecase-tags-exactly.log | grep -B 1 i:stop- | grep TAGS | sort -u | nl >> $LOGFILE
    echo "failed because expected 3 unique tag combinations" >> $LOGFILE
    testfailed
fi
testpassed

teststep "coverage usecase, all/any/random..."
(cat usecase-tags.conf.in; echo 'coverage=usecase(all "i:play.*" then random "i:stop.*" then any "i:play.*")') > usecase-quantifiers.conf
MISSING="alertgamemusic"
COUNTER=0
while ! [ -z "$MISSING" ]; do
    if [ "$COUNTER" == "100" ]; then
        echo "failed because of bad random, tried $COUNTER times but never hit $MISSING" >>$LOGFILE
        testfailed
    fi
    if ! fmbt -l usecase-quantifiers.log usecase-quantifiers.conf >>$LOGFILE 2>&1; then
        cat usecase-quantifiers.conf >> $LOGFILE
        cat usecase-quantifiers.log >> $LOGFILE
        echo "failed because fmbt -l usecase-quantifiers.conf returned non-zero exit status" >> $LOGFILE
        testfailed
    fi
    if [ "$(fmbt-log -f '$as' usecase-quantifiers.log | grep play | wc -l)" != "4" ]; then
        cat usecase-quantifiers.conf >> $LOGFILE
        fmbt-log usecase-quantifiers.log >> $LOGFILE
        echo "failed because four plays expected" >> $LOGFILE
        testfailed
    fi
    if [ "$(fmbt-log -f '$as' usecase-quantifiers.log | grep stop | wc -l)" != "1" ]; then
        cat usecase-quantifiers.conf >> $LOGFILE
        fmbt-log usecase-quantifiers.log >> $LOGFILE
        echo "failed because exactly one stop was expected" >> $LOGFILE
        testfailed
    fi
    STOPPED=$(fmbt-log -f '$ax' usecase-quantifiers.log | tail -n 2 | head -n 1)
    STOPPED=${STOPPED/i:stop-/}
    echo "stopped $STOPPED" >> $LOGFILE
    MISSING=${MISSING/$STOPPED/}
    COUNTER=$(( $COUNTER + 1 ))
done
testpassed

teststep "coverage sum..."
cat > sum.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(7)"
coverage  = "sum(perm(1),
                 perm(1),
                 perm(1))"
pass      = "coverage(5)"
inconc    = "no_progress(10)"
fail      = "steps(100)"
on_pass   = "exit(1)"
on_fail   = "exit(2)"
on_inconc = "exit(0)"
EOF

if ! fmbt -l sum.log sum.conf >>$LOGFILE 2>&1; then
    echo "sum test exit status != 0" >>$LOGFILE
    testfailed
fi

if [ "$(fmbt-log -f '$sc' sum.log | tail -n 1)" != "3.000000" ]; then
    echo "coverage 3.000000 expected, got: $(fmbt-log -f '$sc' sum.log | tail -n 1)" >>$LOGFILE
    testfailed
fi

testpassed

teststep "coverage include..."
cat > cinclude.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc_reg.gt')"
heuristic = "lookahead(1)"
coverage  = "include(iA,perm(2))"
fail      = "steps(3)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
../../src/fmbt cinclude.conf -l cinclude.log 2> cinclude.txt || {
    testfailed
    exit 1
}
testpassed

teststep "coverage include-inconc coverage..."
cat > include-inconc.conf <<EOF
model     = lsts_remote(fmbt-gt -f 'abc_reg.gt')
heuristic = lookahead(2)
coverage  = include("i[AC]", "iB", perm(2))
pass      = coverage(1.1)
fail      = steps(8)
fail      = coverage(usecase("iA[0-9]"))
inconc    = coverage(usecase(("iB" then "iB") and ("iB" then "iC") and not "iA."))
on_pass   = exit(0)
on_fail   = exit(1)
on_inconc = exit(coverage(sum(usecase("iB"),usecase("iC"),usecase("iA[0-9]"))))
on_error  = exit(4)
EOF
fmbt -l include-inconc.log include-inconc.conf >>$LOGFILE 2>&1
exit_status=$?
if [ "$exit_status" != "2" ]; then
    echo "expected exit status 2, got $exit_status from fmbt -l include-inconc.log include-inconc.conf" >>$LOGFILE
    testfailed
    exit 1
fi
testpassed

teststep "coverage exclude + perm regexps..."
cat > exclude-perm-regexps.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(7)"
coverage  = exclude(".*(Insert|Collect).*", perm(2, "i(Choose|Order).*", "iCancel.*"))
pass      = steps(7)
inconc    = coverage(usecase("iCollect.*"))
on_pass   = exit(0)
on_fail   = exit(1)
on_inconc = exit(2)
on_error  = exit(4)
EOF
fmbt -l exclude-perm-regexps.log exclude-perm-regexps.conf >>$LOGFILE  2>&1 || {
    echo "failed to pass fmbt -l exclude-perm-regexps.log exclude-perm-regexps.conf" >> $LOGFILE
    testfailed
}
if [ "$(fmbt-log -f '$sc' exclude-perm-regexps.log | tail -n 1)" != "0.666667" ]; then
    echo "coverage 0.666667 expected, got $(fmbt-log -f '$sc' exclude-perm-regexps.log | tail -n 1)" >>$LOGFILE
    testfailed
fi
testpassed

fmbt-log -f \$sc cinclude.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed

teststep "coverage include regexp..."
cat > cinclude_reg.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc_reg.gt')"
heuristic = "lookahead(1)"
coverage  = "include('iA.*',perm(1))"
fail      = "steps(5)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt cinclude_reg.conf -l cinclude_reg.log 2> cinclude_reg.txt || {
    testfailed
    exit 1
}

fmbt-log -f \$sc cinclude_reg.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed

teststep "coverage exclude..."
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

teststep "coverage exclude regexp..."
cat > cexclude_reg.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc_reg.gt')"
heuristic = "lookahead(1)"
coverage  = "exclude('iA.*',perm(1))"
fail      = "steps(3)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt cexclude_reg.conf -l cexclude_reg.log 2> cexclude_reg.txt || {
    testfailed
    exit 1
}

fmbt-log -f \$sc cexclude_reg.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed


teststep "coverage join..."
cat > cjoin.conf <<EOF
model     = "lsts_remote(fmbt-gt -f 'abc_reg.gt')"
heuristic = "lookahead(1)"
coverage  = "join(iÅ(iA,iA1,iA2,iA3),perm(1))"
fail      = "steps(4)"
pass      = "coverage(1)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF

fmbt cjoin.conf -l cjoin.log 2> cjoin.txt || {
    testfailed
    exit 1
}

fmbt-log -f \$sc cjoin.log|tail -1|while read f
do
if [ 1.000000 != $f ]; then
    testfailed
    exit 1
fi
done
testpassed

teststep "coverage lt, le, gt, ge + steps without params..."
for coverage_cmp in "lt(3, steps)" "le(4, steps)" "gt(steps, 3)" "ge(steps, 4)"; do
    cat > compare.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(3)"
coverage  = "$coverage_cmp"
pass      = "coverage(1)"
fail      = "no_progress(10)"
fail      = "steps(5)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
    cat compare.conf >>$LOGFILE
    if ! fmbt -l compare.log compare.conf >>$LOGFILE 2>&1; then
        echo "fmbt test verdict 'fail', pass expected." >>$LOGFILE
        testfailed
    fi
    fmbt-log compare.log >>$LOGFILE
    echo "step count: $(fmbt-log -f '$ax' compare.log | wc -l)" >>$LOGFILE
    if [ "$(fmbt-log -f '$ax' compare.log | wc -l)" != "4" ]; then
        echo "expected 4 test steps." >>$LOGFILE
        testfailed
    fi
done
testpassed

teststep "coverage if(first, second) + constants..."
cat > if.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(5)"
coverage  = "if( gt(perm(1), 0.5), 13)"
pass      = "coverage(13)"
fail      = "no_progress(5)"
fail      = "steps(50)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
if ! fmbt -l if.log if.conf >>$LOGFILE 2>&1; then
    echo "fmbt verdict pass expected" >>$LOGFILE
    testfailed
fi
if [ "$(fmbt-log -f '$ax' if.log | wc -l)" != "5" ]; then
    echo "expected to execute 5 steps to cover > 50 % from 9 actions" >>$LOGFILE
    testfailed
fi
testpassed

teststep "coverage steps with params + if..."
cat > steps.conf <<EOF
model     = "lsts_remote(fmbt-gt -f coffee.gt)"
heuristic = "lookahead(4)"
coverage  = "if(steps(4,6), 0, perm(1))"
pass      = "coverage(1)"
fail      = "no_progress(10)"
fail      = "steps(50)"
on_pass   = "exit(0)"
on_fail   = "exit(1)"
on_inconc = "exit(2)"
EOF
if ! fmbt -l steps.log steps.conf >>$LOGFILE 2>&1; then
    echo "fmbt verdict pass expected" >>$LOGFILE
    testfailed
fi
if (( $(fmbt-log -f '$ax' steps.log | wc -l) <= 11 )); then
    echo "too few steps, optimal number of steps to cover perm(1) is 12." >>$LOGFILE
    testfailed
fi
if (( $(fmbt-log -f '$sb' steps.log | grep 0.000000 | wc -l) < 5 )); then
    echo "too few 0.000000 coverages observed, at least initial coverage 0" >>$LOGFILE
    echo "and twice a two-step if(0) branch expected." >>$LOGFILE
    testfailed
fi
testpassed
