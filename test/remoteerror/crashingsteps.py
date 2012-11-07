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

# This is a library that can be configured to crash in various
# situations. "BUG" variable should defines WHEN and WHAT kind of
# error should be produced.
# Possible WHENs are "load", "input"
# Possible WHATs are "crash", "raise", "stdout", "stderr"
#
# Example:
# BUG="load-crash"
# from crashingsteps import *

import sys
import os
import signal

g_importer_namespace = sys._getframe().f_back.f_globals

def crashnow():
    os.kill(os.getpid(), signal.SIGSEGV)

def raisenow():
    raise Exception("BogusException from crashingsteps.py")

def stdoutnow():
    sys.stdout.write('This is rubbish-to-stdout\n')
    sys.stdout.flush()

def stderrnow():
    sys.stderr.write('This is rubbish-to-stderr\n')
    sys.stderr.flush()

def check_bug(real_pos):
    if g_importer_namespace['BUG'].split('-')[0] == real_pos:
        eval(g_importer_namespace['BUG'].split('-')[1] + "now()")

check_bug("load")

def iTestStep():
    check_bug("input")
