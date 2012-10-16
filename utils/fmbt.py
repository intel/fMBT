# fMBT, free Model Based Testing tool
# Copyright (c) 2012 Intel Corporation.
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

# Import this to test step implementations written in Python
# in order to enable logging.

# fmbtlog writes given message to the fmbt log (XML)
#         messages can be viewed using format $al of
#         fmbt-log -f '$al' logfile
#
# adapterlog writes given message to the adapter log (plain text)
#         written by remote_python or remote_pyaal, for instance.

# Log function implementations are provided by the adapter
# component such as remote_python or remote_pyaal.

import datetime

g_fmbt_adapterlogtimeformat="%s.%f"

def fmbtlog(msg, flush=True):
    try: file("/tmp/fmbt.fmbtlog", "a").write("%s\n" % (msg,))
    except: pass

def adapterlog(msg, flush=True):
    try: file("/tmp/fmbt.adapterlog", "a").write("%s\n" % (msg,))
    except: pass

def reportOutput(msg):
    try: file("/tmp/fmbt.reportOutput", "a").write("%s\n" % (msg,))
    except: pass

def setAdapterLogTimeFormat(strftime_format):
    """
    Use given time format string in timestamping adapterlog messages
    """
    global g_fmbt_adapterlogtimeformat
    g_fmbt_adapterlogtimeformat = strftime_format

def formatAdapterLogMessage(msg, fmt="%s %s\n"):
    """
    Return timestamped adapter log message
    """
    return fmt % (
        datetime.datetime.now().strftime(g_fmbt_adapterlogtimeformat),
        msg)
