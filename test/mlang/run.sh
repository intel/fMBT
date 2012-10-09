#!/bin/bash

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


# This test runs through the commands in the doc/tutorial.txt.

##########################################
# Setup test environment

cd "$(dirname "$0")"
LOGFILE=/tmp/fmbt.test.aal_tutorial.log
export PATH=../../src:../../utils:$PATH

source ../functions.sh
rm -f $LOGFILE

teststep "brainfuck"
rm -f program.lsts libbrainfuck_memory.so bf2gt
make bf2gt
check_file_exists bf2gt
./bf2gt -i helloworld.bf|fmbt-gt -f - > program.lsts
check_file_exists program.lsts
fmbt-aalc -o brainfuck_memory.cc brainfuck_memory.cc.aal
g++ -fPIC -I ../../src/ -shared -o brainfuck_memory.so brainfuck_memory.cc
check_file_exists brainfuck_memory.so
../../src/fmbt -l brainfuck.log brainfuck.conf 

testpassed
