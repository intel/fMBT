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

new_pass() {
    if [ -a out.lsts ] 
    then
	fmbt-log tmp.log | tee -a pass | relax2.py out.lsts > out_.lsts 
	mv out_.lsts out.lsts
    else 
	(cat fail ; (fmbt-log tmp.log | tee -a pass ) ) | relax2.py > out.lsts
    fi
}

new_fail() {
    mv tmp.log fail.log
    ( (fmbt-log  -f '$as' fail.log;echo fail) | tee fail ; cat pass) | relax2.py > out.lsts
}

PATH=../../src:../../utils:$PATH
start=`date +%s.%N`
# At first we need have a new failure. (1st parameter)
cp $1 tmp.log
new_fail
c=1
heuristic=1
fail=1
pass=0
inc=0
while true
do
    current=`date +%s.%N`
    echo "Current round " $c $current $fail $pass $inc
    echo "scale=4
($current-$start)/$c"|bc
    fmbt -l tmp.log test_shortener.conf -o heuristic\ \=\"lookahead:$heuristic\"
    result=$?
    
    printf "length "
    fmbt-log tmp.log|wc -l

    case $result in
	1)
	    echo "fail"
	    new_fail
	    fail=$(($fail +1))
	    exit 0
	    ;;
	2)
	    echo "pass"
	    new_pass
	    pass=$(($pass +1))
	    ;;
	3)
	    echo "inconclusive"
	    # new_inconclusive
	    heuristic=$(($heuristic+1))
	    inc=$(($inc +1))
	    ;;
	*)
	    echo "ERROR"
	    exit 2
	    ;;
    esac
    c=$(($c+1))
done
