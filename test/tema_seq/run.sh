#!/bin/bash
# coverage_tema_seq, trace growing error trace minimizer
# originally implemented in TEMA (tema.cs.tut.fi)
# Copyright (c) 2011, Heikki Virtanen (heikki.virtanen@tut.fi)
#
# as part of
#
# fMBT, free Model Based Testing tool
# Copyright (c) 2011, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St - Fifth Floor, Boston,
# MA 02110-1301 USA.
#

# Simple smoke test and example of usage.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.tema_seq.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh

cp mkrmdir.conf minimizer.conf
sed -i -r -e 's/^(heuristic.*")[^"]*(".*)/\1lookahead:6b\2/g' minimizer.conf
sed -i -r -e 's/^(coverage.*")[^"]*(".*)/\1tema_seq:org_error.tr\2/g' minimizer.conf

rm -rf minimizer.log adapter.log /tmp/fmbt.mkrmdir

##########################################
# Run the test

teststep "preprocessing error log..."
fmbt-log -f '$as' mkrmdir.log > org_error.tr 2>>$LOGFILE
testpassed

teststep "searching for shorter error trace..."
fmbt -L minimizer.log minimizer.conf < /dev/null > /dev/null
ORIGLEN=$(wc -l < org_error.tr)
NEWLEN=$(fmbt-log -f '$as' minimizer.log | wc -l)
echo "Original error trace: $ORIGLEN"  >>$LOGFILE
echo "Resulting error trace: $NEWLEN"  >> $LOGFILE
if (( $NEWLEN < $ORIGLEN )); then
    testpassed
else
    echo "Error: did not find shorter error trace" >> $LOGFILE
    testfailed
fi
