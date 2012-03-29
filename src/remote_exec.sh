#!/bin/sh

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

LOGFILE=/tmp/remote_exec.log

usage() {
    echo "remote_exec.sh adapter for fMBT"
    echo ""
    echo "Usage: remote_exec.sh [options]"
    echo ""
    echo "Options:"
    echo "  -c <string>"
    echo "          execute the given string before starting executing"
    echo "          actions. Example: remote_exec.sh -c '. ./myteststeps.sh\'"
    echo ""
    echo "  -h      print this help"
    echo ""
    echo "  -l <filename>"
    echo "          write (overwrite) log to the file instead of $LOGFILE"
    echo ""
    echo "  -L <filename>"
    echo "          write (append) log to the file instead of $LOGFILE"
}

# Shell commands sent to this adapter are executed with this shell:
SHELL=/bin/sh

while getopts c:hl:L: opt
do
    case $opt in
        c) eval $OPTARG >> $LOGFILE 2>&1 ;;
        l) LOGFILE=$OPTARG; echo -n "" > $LOGFILE ;;
        L) LOGFILE=$OPTARG ;;
        h | \?) usage; exit 1 ;;
    esac
done
shift $(expr $OPTIND - 1)

echo $(date +"%F %T") $0 adapter started >> $LOGFILE

# This script should work on many environments, some of them providing
# Python, some Perl, some only sed
URLDECODER="python -c 'import sys; import urllib; sys.stdout.write(urllib.unquote(sys.stdin.read()))'"
if [ "$(echo "1%2E5" | eval $URLDECODER)" != "1.5" ]; then
    echo Warning: Python URL decoder does not work >> $LOGFILE
    URLDECODER="perl -pe 's/%([0-9A-Fa-f][0-9A-Fa-f])/chr(hex(\$1))/eg'"
    if [ "$(echo "1%2E5" | eval $URLDECODER)" != "1.5" ]; then
        echo Warning: Even hackish Perl URL decoder does not work >> $LOGFILE
        # TODO: this should be more complete:
        URLDECODER="sed -e 's:%20: :g' -e 's:%24:$:g' -e 's:%2A:*:g' -e 's:%2C:,:g' -e 's:%2E:.:g' -e 's:%2F:/:g' -e 's:%3B:;:g' -e 's:%3C:<:g' -e 's:%3D:=:g' -e 's:%3E:>:g' -e s:%27:\':g -e 's:%5E:^:g'"
    fi
fi

read count
var=0

while [ "$var" -lt "$count" ]
do
    read encodedAction
    # Shell command may be prefixed with "i:" to force it to be an
    # input action in the test model. In this case remove the prefix.
    encodedAction=${encodedAction#i%3A}
    # urldecode:
    eval s${var}=\"$( echo $encodedAction | eval $URLDECODER )\" 
    echo -n "s${var}: " >> $LOGFILE
    eval unencodedAction=\$s${var}
    echo $unencodedAction  >> $LOGFILE
    var=`expr $var + 1`
done 

export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin

while read a
do
     echo "Evaluating s${a}" >> $LOGFILE
     eval run=\$s${a} >> $LOGFILE 2>&1
     echo "Executing $a: '$run'" >> $LOGFILE
     if ( eval "$run" >> $LOGFILE 2>&1 ); then
         echo "Reporting $a" >> $LOGFILE
         echo $a 1>&2
         sync # flush stdout => echoed $a will be written to stderr
     else
         echo "Returned exit status $?, reporting error" >> $LOGFILE
         echo 0 1>&2
         sync
     fi
done
