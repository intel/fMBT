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

cp mkrmdir.conf minimizer.conf
sed -i -r -e 's/^(heuristic.*")[^"]*(".*)/\1greedy:6b\2/g' minimizer.conf
sed -i -r -e 's/^(coverage.*")[^"]*(".*)/\1tema_seq:org_error.tr\2/g' minimizer.conf

rm -rf minimizer.log adapter.log /tmp/fmbt.mkrmdir

../../utils/fmbt-log -f '$as' mkrmdir.log > org_error.tr
../../src/fmbt -L minimizer.log minimizer.conf < /dev/null

echo "Original error trace:" $(wc -l < org_error.tr)
echo "Resulting error trace:" $(../../utils/fmbt-log -f '$as' minimizer.log | wc -l)
