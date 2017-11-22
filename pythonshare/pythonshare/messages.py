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

# This library defines message types for pythonshare client-server
# messaging.
import zlib

RECV_CAP_DATA_INFO = 1
RECV_CAP_COMPRESSION = 1 << 1

MSG_STRING_FIELD_MAX_LEN = 1024

def crc(s):
    """returns crc32 as an 8-character hex for a string"""
    return hex(zlib.crc32(s) & 0xffffffff)[2:].zfill(8)

class Unpicklable(object):
    def __init__(self, obj):
        self._string = str(obj)
    def __str__(self):
        return 'Unpicklable("%s")' % (self._string,)

class Unloadable(object):
    def __init__(self, obj):
        self._string = str(obj)
    def __str__(self):
        return 'Unloadable("%s")' % (self._string,)

class Auth_rv(object):
    def __init__(self, success, errormsg=""):
        self.success = success
        if not errormsg and not success:
            self.errormsg = "Permission denied"
        else:
            self.errormsg = errormsg
    def __str__(self):
        return 'Auth_rv(success=%s, errormsg=%s)' % (
            repr(self.success), repr(self.errormsg))

class Exec(object):
    def __init__(self, namespace, code, expr, lock=True, async=False, recv_caps=0):
        self.namespace = namespace
        self.code = code
        self.expr = expr
        self.lock = lock
        self.async = async
        self.recv_caps = recv_caps # capabilities of the receiver of the Exec_rv
    def recv_cap_data_info(self):
        """returns True if Exec can be responded with Data_info+Exec_rv"""
        # If this class has been unpickled from old pythonshare connection,
        # the recv_caps attribute will not be present.
        if not hasattr(self, "recv_caps"):
            self.recv_caps = 0
        return self.recv_caps
    def set_recv_cap_data_info(self, value):
        current_caps = getattr(self, "recv_caps", 0)
        if value: # set to true
            self.recv_caps = current_caps | RECV_CAP_DATA_INFO
        elif self.recv_cap_data_info(): # set to false
            self.recv_caps = current_caps - RECV_CAP_DATA_INFO
    def __str__(self):
        self.recv_cap_data_info() # make sure recv_caps exist
        return ('Exec(namespace=%r, code=%r, expr=%r, '
                'lock=%r, async=%r, recv_caps=%r)' % (
                    self.namespace, self.code, self.expr,
                    self.lock, self.async, self.recv_caps))

class Exec_rv(object):
    def __init__(self, code_exc, expr_exc, expr_rv):
        self.code_exc = code_exc
        self.expr_exc = expr_exc
        self.expr_rv = expr_rv
    def __str__(self):
        rv = self.expr_rv
        if not MSG_STRING_FIELD_MAX_LEN is None and isinstance(rv, basestring):
            if len(rv) > MSG_STRING_FIELD_MAX_LEN:
                rv = (rv[:MSG_STRING_FIELD_MAX_LEN/2] +
                      ("...[%s B, CRC %s]..." % (len(rv), crc(rv))) +
                      rv[-MSG_STRING_FIELD_MAX_LEN/2:])
        return 'Exec_rv(code_exc="%s", expr_exc="%s", rv=%r)' % (
            self.code_exc, self.expr_exc, rv)

# Data_info messages precede large data transmissions (for example
# before large Exec_rv:s) to allow hubs and senders/receivers optimize
# their behavior.
class Data_info(object):
    def __init__(self, data_type, data_length, data_format):
        self.data_type = data_type
        self.data_length = data_length
        self.data_format = data_format
    def __str__(self):
        return 'Data_info(data_type=%r, data_length=%r, data_format=%r)' % (
            self.data_type, self.data_length, self.data_format)

class Async_rv(object):
    def __init__(self, ns=None, rvid=None):
        self.ns = ns
        self.rvid = rvid
    def __str__(self):
        return 'Async_rv(ns="%s", rvid="%s")' % (
            self.ns, self.rvid)

class Register_ns(object):
    def __init__(self, ns):
        self.ns = ns
    def __str__(self):
        return 'Register_ns(ns="%s")' % (
            self.ns,)

class Drop_ns(object):
    def __init__(self, ns):
        self.ns = ns
    def __str__(self):
        return 'Drop_ns(ns="%s")' % (
            self.ns,)

class Request_ns(object):
    def __init__(self, ns):
        self.ns = ns
    def __str__(self):
        return 'Request_ns(ns="%s")' % (
            self.ns,)

class Ns_rv(object):
    def __init__(self, status, errormsg=None):
        self.status = status
        self.errormsg = errormsg
    def __str__(self):
        return 'Ns_rv(status="%s", errormsg="%s")' % (
            self.status, errormsg)

class Server_ctl(object):
    def __init__(self, command, *args):
        self.command = command
        self.args = args
    def __str__(self):
        return 'Server_ctl(command=%s, args=%s)' % (
            repr(self.command),
            repr(self.args))

class Server_ctl_rv(object):
    def __init__(self, status, message):
        self.status = status
        self.message = message
    def __str__(self):
        return 'Server_ctl_rv(status=%s, message=%s)' % (
            repr(self.status),
            repr(self.message))
