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

# This library provides Python API for connecting to pythonshare
# servers, sending code for remote execution and exporting/importing
# namespaces.

import socket
import cPickle

import pythonshare
from pythonshare.messages import Exec, Exec_rv, Async_rv, Register_ns, Request_ns

class Connection(object):
    def __init__(self, host, port):
        """
        Connect to Python share server running on host:port.
        """
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((host, port))
        self._from_server = self._s.makefile("r")
        self._to_server = self._s.makefile("w")

    def make_local(self, rv):
        if isinstance(rv, Exec_rv):
            if rv.code_exc:
                raise pythonshare.RemoteExecError(rv.code_exc)
            elif rv.expr_exc:
                raise pythonshare.RemoteEvalError(rv.expr_exc)
            else:
                rv = rv.expr_rv
        return rv

    def exec_in(self, namespace, code, expr=None, async=False, lock=True):
        """Execute code in the namespace.

        Parameters:

          namespace (string)
                  namespace in which the code and the expression (if
                  given) will be executed.

          code (string)
                  Python code to be executed in the namespace.

          expr (string, optional)
                  expression to be evaluated in the namespace after
                  executing the code.

          async (boolean, optional)
                  If true, execute code and expr asynchronously. If
                  so, handle to the return value (Async_rv) will be
                  returned.

        Returns return value from expr or None.

        Raise RemoteExecError or RemoteEvalError if code or expr caused
        an exception in remote end, respectively.

        """
        try:
            cPickle.dump(Exec(namespace, code, expr, async=async, lock=lock), self._to_server)
            self._to_server.flush()
            return self.make_local(cPickle.load(self._from_server))
        except EOFError:
            raise pythonshare.PythonShareError(
                'no connection to namespace "%s"' % (namespace,))

    def eval_in(self, namespace, expr, async=False, lock=True):
        return self.exec_in(namespace, "", expr, async=async, lock=lock)

    def read_rv(self, async_rv, timeout=0):
        """Read return value of async call.

        Parameters:

          async_rv (string or Async_rv object)
                  Handle to asynchronous return value, created by
                  async exec_in or eval_in.

          timeout (float or integer, optional)
                  -1: block until return value is ready and return it.
                  0: returns pythonshare.Busy immediately if return
                  value is not readable yet.
                  > 0: wait until this timeout (NOT IMPLEMENTED).
                  The defualt is 0.
        """
        if isinstance(async_rv, str):
            async_rv = eval(async_rv)
        rv = self.eval_in(async_rv.ns, "pythonshare_ns.read_rv(%s)" % (async_rv,))
        return rv

    def export_ns(self, namespace):
        """Export namespace to remote peer

        Parameters:

          namespace (string)
                  Namespace to be exported, can be local or
                  remote to current host.

        Returns True on success or raises an exception.  If succeeded,
        this connection becomes a server for requests from remote
        peer. (The remote peer accesses registered namespace through
        this connection object.)
        """
        cPickle.dump(Register_ns(namespace), self._to_server)
        self._to_server.flush()
        ns_rv = cPickle.load(self._from_server)
        if ns_rv.status:
            return True
        else:
            raise PythonShareError(ns_rv.errormsg)

    def import_ns(self, namespace):
        """
        """
        cPickle.dump(Request_ns(namespace), self._to_server)
        self._to_server.flush()
        ns_rv = cPickle.load(self._from_server)
        if ns_rv.status:
            return True
        else:
            raise PythonShareError(ns_rv.errormsg)

    def poll_rvs(self, namespace):
        return self.eval_in(namespace, "pythonshare_ns.poll_rvs()",
                            async=False, lock=False)

    def close(self):
        pythonshare._close(self._to_server, self._from_server, self._s)

    def getpeername(self):
        return self._s.getpeername()
