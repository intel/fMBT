#
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

# fmbtparsers.py implements Python interface to the fmbt_parsers.so C
# library.

import ctypes
import os

_c_int    = ctypes.c_int
_c_char_p = ctypes.c_char_p
_c_func   = ctypes.CFUNCTYPE

_libpath = [os.path.dirname(__file__),
            os.path.dirname(__file__) + "/../src/.libs"]

def load(filename):
    if filename.endswith(".lsts"):
        load_lts(filename)
    elif filename.endswith(".xrules"):
        load_xrules(filename)

def xrules_result_action(callback):
    callback.c = _c_func(None, _c_char_p)(callback)
    clib.xrules_result_action(callback.c)

def lts_action(callback):
    callback.c = _c_func(None, _c_int, _c_char_p)(callback)
    clib.lts_action(callback.c)

# TODO: the rest of the callbacks

for _dirname in _libpath:
    try:
        clib = ctypes.CDLL(_dirname + os.sep + "fmbt_cparsers.so")
        break
    except: pass
else:
    raise ImportError("fmbtparsers.py cannot find fmbt_cparsers.so")

load_lts = clib.lts_load

load_xrules = clib.xrules_load
