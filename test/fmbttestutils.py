#!/usr/bin/env python2
#
# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions of the GNU Lesser General Public
# License, version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St - Fifth Floor, Boston, MA
# 02110-1301 USA.

"""Cross-platform utilities for fMBT tests

Usage: python fmbttestutils.py [options]

Options:
  -p, --pid-exists=PID
          exit successfully if a process with PID is exists
          in the system. Otherwise exit with non-zero error code.
"""

import getopt
import os
import sys

if os.name == "nt":
    import ctypes

def pid_exists(pid):
    """Returns True if a process with PID is running, otherwise False"""
    if os.name == "nt":
        return _pid_exists_on_windows(pid)
    else:
        return _pid_exists_on_linux(pid)

def _pid_exists_on_linux(pid):
    try:
        os.kill(pid, 0)
    except OSError, e:
        if e.errno == 3:
            return False
    return True

def _pid_exists_on_windows(pid):
    ERROR_ACCESS_DENIED = 5
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    hProc = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if hProc == 0:
        if ctypes.windll.kernel32.GetLastError() == 5:
            # Access denied, process exists
            return True
        else:
            return False
    else:
        ctypes.windll.kernel32.CloseHandle(hProc)
        return True

if __name__ == "__main__":
    opts, remainder = getopt.getopt(
        sys.argv[1:],
        "hp:",
        ["help", "pid-exists="])
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print __doc__
            sys.exit(0)
        elif opt in ['-p', '--pid-exists']:
            if pid_exists(int(arg)):
                sys.exit(0)
            else:
                sys.exit(1)
