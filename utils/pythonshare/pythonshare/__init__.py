# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
#
# Author: antti.kervinen@intel.com
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

import client
import server
import messages
import urlparse as _urlparse

from messages import Exec, Exec_rv

# Connection = client.Connection
default_port = 8089 # PY

class PythonShareError(Exception):
    pass

class AuthenticationError(PythonShareError):
    pass

class RemoteExecError(PythonShareError):
    pass

class RemoteEvalError(PythonShareError):
    pass

class AsyncStatus(object):
    pass

class InProgress(AsyncStatus):
    pass

# Misc helpers for client and server
def _close(*args):
    for a in args:
        try:
            a.close()
        except (socket.error, IOError):
            pass

def connection(hostspec, password=None):
    if not "://" in hostspec:
        hostspec = "socket://" + hostspec
    scheme, netloc, _, _, _ = _urlparse.urlsplit(hostspec)
    if scheme == "socket":
        if ":" in netloc:
            host, port = netloc.split(":")
        else:
            host, port = netloc, default_port
        return client.Connection(host, int(port), password=password)
    else:
        raise ValueError('invalid url "%s"' % (hostspec,))
