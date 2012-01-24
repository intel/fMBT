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

echo $(date +"%F %T") $0 adapter started > $LOGFILE

read count
var=0

while [ "$var" -lt "$count" ]
do
    read encodedAction
    # urldecode:
    eval s${var}=\"$( echo $encodedAction | sed -e 's:%2F:/:g' -e 's:%20: :g' -e 's:%5E:^:g' -e 's:%3D:=:g' -e 's:%2A:*:g' -e 's:%24:$:g' -e 's:%2C:,:g' -e 's:%3B:;:g' -e s:%27:\':g )\"
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
     /bin/ash -c "$run" >> $LOGFILE 2>&1
     echo $a 1>&2
     sync # flush stdout => echoed $a will be written to stderr
     echo "Reporting $a" >> $LOGFILE
done
