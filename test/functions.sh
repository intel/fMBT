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


# This file includes test reporting functions for test scripts.

teststep() {
    printf "%-50s" "$1"
    echo "##########################################" >>$LOGFILE
    echo "# $1" >>$LOGFILE
}

testpassed() {
    printf "passed.\n"
    echo "# passed." >>$LOGFILE
}

testfailed() {
    printf "failed, see $LOGFILE\n"
    echo "# failed." >>$LOGFILE
    exit 1
}

check_file_exists() {
    FILENAME=$1
    if [ ! -f $FILENAME ]; then
        echo "$FILENAME does not exist." >> $LOGFILE
        testfailed
    fi
}

check_minimum_num_of_lines() {
    FILENAME=$1
    MINIMUM_NUMOFLINES=$2

    check_file_exists $FILENAME

    FOUND_LINES=$(wc -l $FILENAME | awk '{print $1}')
    if  [ $FOUND_LINES -lt $MINIMUM_NUMOFLINES ]; then
        echo "$FILENAME too short." >> $LOGFILE
        echo "    $MINIMUM_NUMOFLINES lines required," >> $LOGFILE
        echo "    $FOUND_LINES lines found." >> $LOGFILE
        testfailed
    fi
}

if [ -z "$SKIP_PATH_CHECKS" ]; then

    teststep "check that utils/fmbt-gt is used..."
    dirandfmbtgt=$(which fmbt-gt | sed 's:.*\(utils/.*\):\1:')
    echo "fmbt-gt: $dirandfmbtgt" >> $LOGFILE
    if [ "$dirandfmbtgt" != "utils/fmbt-gt" ]; then
        testfailed
    fi
    testpassed
    
    teststep "check that fmbt is used from source tree..."
    dirandfmbt=$(which fmbt | sed 's:.*\(src/.*\):\1:')
    echo "using: $dirandfmbt" >> $LOGFILE
    echo "fmbt: $dirandfmbt" >> $LOGFILE
    if [ "$dirandfmbt" != "src/fmbt" ] && [ "$dirandfmbt" != "./fmbt" ]; then
        testfailed
    fi
    testpassed
    
    teststep "check working python version..."
    pyver=$(/usr/bin/env python --version 2>&1 | awk '{if ($2 >= "2.6") print "ok"}')
    if [ "$pyver" != "ok" ]; then
        echo "Python >= 2.6 required, you run $(/usr/bin/env python --version 2>&1)" >> $LOGFILE
        testfailed
    fi
    testpassed

fi
