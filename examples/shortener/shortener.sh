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

usage() {
    echo 'Usage: shortener [-a] [-s cmd] [-n num] origconf errorlog'
    echo 'Options:'
    echo '  -a       aggressive dropping of candidates (fast, but may not'
    echo '           find minimal error trace if there are disarming test steps)'
    echo '  -n num   run num rounds'
    echo '  -s cmd   setup command run before every execution of fmbt'
}

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
    touch pass
    ( (fmbt-log -f '$ax--FMBT-SEP--$as--FMBT-SEP--$tv' fail.log | awk -F '--FMBT-SEP--' '{if ($1!="" && $3=="")print $1; else if ($2!="") print $2;verdict=$3}END{print verdict}') | tee fail ; cat pass) | relax2.py > out.lsts
}

PATH=../../src:../../utils:../../../src:../../../utils:$PATH
start=`date +%s.%N`

RUN_ROUNDS=unlimited
AGGRESSIVE=0
while getopts ahs:n: opt
do
    case $opt in
        a) AGGRESSIVE=1 2>&1 ;;
        s) SETUP_CMD="$OPTARG" ;;
        n) RUN_ROUNDS=$OPTARG ;;
        h | \?) usage; exit 0 ;;
    esac
done
shift $(expr $OPTIND - 1)
ORIG_CONF="$1"
ORIG_LOG="$2"

if [ ! -f "$ORIG_CONF" ]; then
    usage
    echo "Test configuration file missing."
    exit 1
fi
if [ ! -f "$ORIG_LOG" ]; then
    usage
    echo "Failing test log missing."
    exit 1
fi

# At first we need have a new failure. (1st parameter)
cp "$ORIG_LOG" tmp.log

SHORTENER_CONF="shortener.conf"

# Generate shortener configuration based on orig conf
STOP_AT_STEP=$(fmbt-log -f '$sn' tmp.log | tail -n 1)
grep "^model" "$ORIG_CONF"                   > "$SHORTENER_CONF"
grep "^adapter" "$ORIG_CONF"                >> "$SHORTENER_CONF"
echo 'coverage = "mapper(shortener.crules)"' >> "$SHORTENER_CONF"
echo ''                                     >> "$SHORTENER_CONF"
echo 'pass = "coverage(1.0)"'                >> "$SHORTENER_CONF"
echo "inconc = \"steps($STOP_AT_STEP)\""     >> "$SHORTENER_CONF"
echo ''                                     >> "$SHORTENER_CONF"
echo 'on_fail   = "exit(1)"'                 >> "$SHORTENER_CONF"
echo 'on_pass   = "exit(2)"'                 >> "$SHORTENER_CONF"
echo 'on_inconc = "exit(3)"'                 >> "$SHORTENER_CONF"
echo 'on_error  = "exit(4)"'                 >> "$SHORTENER_CONF"

# Generate shortener crules for passing error trace candidate
# model to the "short" coverage module.
cat > shortener.crules <<EOF
1 = "short,lsts(out.lsts)"

"(.*)"              -> (1, "(\$1)")
EOF

rm -f out.lsts
rm -f pass
new_fail
c=1
heuristic=5
fail=1
pass=0
inc=0
while [ "$RUN_ROUNDS" == "unlimited" ] || (( $c <= $RUN_ROUNDS ))
do
    current=`date +%s.%N`
    echo "Current round " $c $current $fail $pass $inc
    echo "scale=4
($current-$start)/$c"|bc
    eval $SETUP_CMD

    heuristic=1

    fmbt -l tmp.log "$SHORTENER_CONF" -o heuristic\ \=\"lookahead\($heuristic\)\"
    result=$?
    
    printf "length "
    fmbt-log tmp.log|wc -l

    case $result in
	1)
	    echo "fail"
	    new_fail
	    fail=$(($fail +1))
	    # exit 0
	    ;;
	2)
	    echo "pass"
	    new_pass
	    pass=$(($pass +1))
	    ;;
	3)
	    echo "inconclusive"
            if [ "$AGGRESSIVE" == "1" ]; then
                sed -e 's/inconclusive/pass/g' -i tmp.log
                new_pass
            fi
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
