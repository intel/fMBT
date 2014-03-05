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

class Unpicklable(object):
    def __init__(self, obj):
        self._string = str(obj)
    def __str__(self):
        return 'Unpicklable("%s")' % (self._string,)

class Auth_rv(object):
    def __init__(self, success):
        self.success = success
    def __str__(self):
        return 'Auth_rv(success=)' % (
            self.success)

class Exec(object):
    def __init__(self, namespace, code, expr, lock=True, async=False):
        self.namespace = namespace
        self.code = code
        self.expr = expr
        self.lock = lock
        self.async = async
    def __str__(self):
        return ('Exec(namespace="%s", code="%s", expr="%s", '
                'lock=%s, async=%s)' % (
                self.namespace, self.code, self.expr,
                self.lock, self.async))

class Exec_rv(object):
    def __init__(self, code_exc, expr_exc, expr_rv):
        self.code_exc = code_exc
        self.expr_exc = expr_exc
        self.expr_rv = expr_rv
    def __str__(self):
        return 'Exec_rv(code_exc="%s", expr_exc="%s", rv=%s)' % (
            self.code_exc, self.expr_exc, self.expr_rv)

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
