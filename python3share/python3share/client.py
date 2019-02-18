# fMBT, free Model Based Testing tool
# Copyright (c) 2013-2015, Intel Corporation.
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

"""python3share.client - interface for executing code on pythonshare servers
"""

import socket

import python3share
from python3share.messages import \
    Exec, Exec_rv, Async_rv, Register_ns,\
    Request_ns, Drop_ns, Ns_rv, Server_ctl, Server_ctl_rv, Data_info

class Connection(object):
    """Connection to a Pythonshare server.

    Example: connect to a server that is listening to port 8089 on localhost.
    Execute *code* and evaluate *expression* on the default namespace on the
    remote server.

    c = Connection("localhost", 8089)
    c.exec_(code)
    c.eval_(expression)

    Results of executed code are kept on the server after the
    connection is closed.

    Example: Register code that is executed in namespace "goodbye" after
    closing the connection:

    c.exec_in("goodbye", 'pythonshare_ns.exec_on_disconnect("code")')
    """
    def __init__(self, host_or_from_server, port_or_to_server,
                 password=None, namespace="default"):
        """Connect to a pythonshare server

        The server is listening to connections at host:port, or it can be
        communicated via file-like objects from_server and to_server.

        Parameters:

          host_or_from_server (string or file-like object)
                  string: host
                  file: file for receiving messages from the server

          port_or_to_server (int or file-like object)
                  int: port number
                  file: file for sending messages to the server

          password (string, optional)
                  server password. The default is None, that is,
                  do not send password to the server when connecting.

          namespace (string, optional)
                  the default namespace that is used on eval_() and exec_().
                  The default is "default".
        """
        self.set_namespace(namespace)

        if isinstance(host_or_from_server, str) and isinstance(port_or_to_server, int):
            host = host_or_from_server
            port = port_or_to_server
            python3share._check_hook("before:client.socket.connect", {"host": host, "port": port})
            self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._s.connect((host, port))
            self._from_server = self._s.makefile("rb")
            self._to_server = self._s.makefile("wb")
        elif isinstance(host_or_from_server, file) and isinstance(port_or_to_server, file):
            self._s = None
            self._to_server = port_or_to_server
            self._from_server = host_or_from_server
        else:
            raise ValueError("invalid host:port (str:int) or to_server:from_server (file:file)")

        if password:
            # authenticate to server
            python3share._send(password, self._to_server)
            auth_rv = python3share._recv(self._from_server)
            try:
                auth_ok = auth_rv.success
            except AttributeError:
                auth_ok = False
            if not auth_ok:
                raise python3share.AuthenticationError("Permission denied")

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def make_local(self, rv):
        if isinstance(rv, Exec_rv):
            if rv.code_exc:
                raise python3share.RemoteExecError(rv.code_exc)
            elif rv.expr_exc:
                raise python3share.RemoteEvalError(rv.expr_exc)
            else:
                rv = rv.expr_rv
        return rv

    def exec_(self, code, **kwargs):
        """Execute code in the default namespace.

        See exec_in for optional parameters."""
        return self.exec_in(self._ns, code, **kwargs)

    def exec_in(self, namespace, code, expr=None, async_=False, lock=True):
        """Execute code in a namespace.

        Parameters:

          namespace (string)
                  namespace in which the code and the expression (if
                  given) will be executed.

          code (string)
                  Python code to be executed in the namespace.

          expr (string, optional)
                  expression to be evaluated in the namespace after
                  executing the code.

          async_ (boolean, optional)
                  If true, execute code and expr asynchronously. If
                  so, handle to the return value (Async_rv) will be
                  returned. The default is False.

          lock (boolean, optional)
                  lock the namespace from others until this execution
                  has finished. The default is True.

        Returns return value from expr or None.

        Raise RemoteExecError or RemoteEvalError if code or expr caused
        an exception in remote end, respectively.

        """
        if namespace == None:
            namespace = self.namespace()
        python3share._check_hook("before:client.exec_in", {"code": code, "expr": expr, "namespace": namespace, "async_": async_, "lock": lock})
        try:
            python3share._send(Exec(
                namespace, code, expr, async_=async_, lock=lock,
                recv_caps=python3share.messages.RECV_CAP_COMPRESSION), self._to_server)
            response = python3share._recv_with_info(self._from_server)
            return self.make_local(response)
        except EOFError:
            raise python3share.PythonShareError(
                'No connection to namespace "%s"' % (namespace,))

    def eval_(self, expr, **kwargs):
        """Evaluate expr in the default namespace.

        See eval_in for optional parameters."""
        return self.eval_in(self._ns, expr, **kwargs)

    def eval_in(self, namespace, expr, async_=False, lock=True):
        """Evaluate expr in a namespace.

        Parameters:

          namespace (string)
                  namespace in which the expression will be evaluated.

          expr (string)
                  Python expression.

          async_ (boolean, optional)
                  If True, expression will be evaluated asynchronously
                  and a handle to the return value (Async_rv) will be
                  returned.

          lock (boolean, optional)
                  lock the namespace from others until this execution
                  has finished. The default is True.

        Returns return value of the expr.

        Raises RemoteEvalError if expr caused an exception.
        """
        return self.exec_in(namespace, "", expr, async_=async_, lock=lock)

    def read_rv(self, async_rv, timeout=0):
        """Read return value of async call.

        Parameters:

          async_rv (string or Async_rv object)
                  Handle to asynchronous return value, created by
                  async exec_in or eval_in.

          timeout (float or integer, optional)
                  -1: block until return value is ready and return it.
                  0: returns python3share.Busy immediately if return
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
        python3share._send(Register_ns(namespace), self._to_server)
        rv = python3share._recv(self._from_server)
        if isinstance(rv, Ns_rv) and rv.status:
            return True
        else:
            raise python3share.PythonShareError(rv.errormsg)

    def import_ns(self, namespace):
        """
        """
        python3share._send(Request_ns(namespace), self._to_server)
        rv = python3share._recv(self._from_server)
        if isinstance(rv, Ns_rv) and rv.status:
            return True
        else:
            raise python3share.PythonShareError(rv.errormsg)

    def drop_ns(self, namespace):
        """Delete namespace from the remote peer

        Parameters:

          namespace (string)
                  Namespace to be dropped, can be local or
                  remote to the server.

        Returns True on success or raises an exception.
        """
        python3share._send(Drop_ns(namespace), self._to_server)
        rv = python3share._recv(self._from_server)
        if isinstance(rv, Ns_rv) and rv.status:
            return True
        else:
            raise python3share.PythonShareError(rv.errormsg)

    def unlock_ns(self, namespace):
        """Unlock namespace on the remote peer

        Parameters:

          namespace (string)
                  Namespace to be unlocked, can be local or
                  remote to the server.

        Returns True on success or raises an exception.
        """
        python3share._send(Server_ctl("unlock", namespace), self._to_server)
        rv = python3share._recv(self._from_server)
        if isinstance(rv, Server_ctl_rv) and rv.status == 0:
            return True
        else:
            raise python3share.PythonShareError(rv.message)

    def poll_rvs(self, namespace=None):
        """Poll available async return values from namespace.

        Parameters:

          namespace (string, optional)
                  namespace from which return values are queried.
                  The default is returned by namespace().

        Example:

        rv = c.eval_("time.sleep(1)", async=True)
        print c.poll_rvs(rv.ns)
        time.sleep(1)
        print c.poll_rvs(rv.ns)
        print c.read_rv(rv)
        """
        return self.eval_in(namespace, "pythonshare_ns.poll_rvs()",
                            async_=False, lock=False)

    def close(self):
        python3share._check_hook("before:client.socket.close", {"socket": self._s})
        python3share._close(self._to_server, self._from_server, self._s)

    def kill_server(self, namespace=None):
        """Send server shutdown message"""
        if namespace == None:
            namespace = self.namespace()
        python3share._send(Server_ctl("die", namespace), self._to_server)
        return True

    def ls_local(self):
        """List local namespaces on the server"""
        return self.eval_("pythonshare_ns.local_nss()")

    def ls_remote(self, **kwargs):
        """List remote namespaces on the server"""
        return self.eval_("pythonshare_ns.remote_nss(%r)" % (kwargs,))

    def ns_type(self, ns):
        return self.eval_("pythonshare_ns.ns_type(%s)" % (repr(ns),))

    def namespace(self):
        """Return default namespace"""
        return self._ns

    def set_namespace(self, ns):
        """Set new default namespace"""
        self._ns = ns

    def getpeername(self):
        if self._s:
            return self._s.getpeername()
        else:
            return (getattr(self._to_server, "name", None),
                    getattr(self._from_server, "name", None))
