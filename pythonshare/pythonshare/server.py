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

# This library implements pythonshare server functionality.

import datetime
import getopt
import hashlib
import os
import platform
import socket
import sys
import tempfile
import cPickle
import thread
import traceback
import urlparse

import pythonshare
messages = pythonshare.messages
client = pythonshare.client

on_windows = (os.name == "nt")
has_os_fdatasync = hasattr(os, "fdatasync")

opt_debug_stdout_limit = 240
opt_log_fd = None
opt_allow_new_namespaces = True

def timestamp():
    if on_windows:
        rv = "%.6f" % (
            (datetime.datetime.now() -
             datetime.datetime(1970,1,1)).total_seconds(),)
    else:
        rv = datetime.datetime.now().strftime("%s.%f")
    return rv

def daemon_log(msg):
    formatted_msg = "%s %s\n" % (timestamp(), msg)
    if opt_log_fd != None:
        os.write(opt_log_fd, formatted_msg)
        if has_os_fdatasync:
            os.fdatasync(opt_log_fd)
    if opt_debug and opt_debug_stdout_limit != 0:
        if opt_debug_stdout_limit > 0 and len(formatted_msg) > opt_debug_stdout_limit:
            sys.stdout.write(formatted_msg[:opt_debug_stdout_limit-3] + "...\n")
        else:
            sys.stdout.write(formatted_msg)
        sys.stdout.flush()

def code2string(code):
    return "\n".join(
        ["%-4s %s" % (li+1, l) for li, l in enumerate(code.splitlines())])

def exception2string(exc_info):
    return ''.join(traceback.format_exception(*exc_info))

class Pythonshare_ns(object):
    """
    Pythonshare services inside a namespace
    """
    def __init__(self, ns):
        self.ns = ns
        self._on_disconnect = []
        self._on_delete = []

    def on_disconnect(self):
        """
        Return codes that will be executed when a client has disconnected.
        """
        return self._on_disconnect

    def exec_on_disconnect(self, code, any_connection=False):
        """
        Add code that will be executed when client has disconnected.
        """
        if not any_connection:
            conn_id = _g_executing_pythonshare_conn_id
        else:
            conn_id = None
        self._on_disconnect.append((conn_id, code))

    def set_on_disconnect(self, list_of_code):
        """
        Replace all "on disconnect" codes with new list of codes.
        """
        self._on_disconnect = list_of_code

    def call_on_disconnect(self, conn_id):
        for setter_conn_id, code in self._on_disconnect:
            if not setter_conn_id or setter_conn_id == conn_id:
                exec_msg = messages.Exec(self.ns, code, None)
                if opt_debug:
                    daemon_log("on disconnect %s: %s" % (conn_id, exec_msg,))
                rv = _local_execute(exec_msg)
                if opt_debug:
                    daemon_log("on disconnect rv: %s" % (rv,))
                if setter_conn_id == conn_id:
                    self._on_disconnect.remove((conn_id, code))

    def read_rv(self, async_rv):
        """
        Return and remove asynchronous return value.
        """
        if self.ns != async_rv.ns:
            raise ValueError("Namespace mismatch")
        if (async_rv.ns in _g_async_rvs and
            async_rv.rvid in _g_async_rvs[async_rv.ns]):
            rv = _g_async_rvs[async_rv.ns][async_rv.rvid]
            if not isinstance(rv, pythonshare.InProgress):
                del _g_async_rvs[async_rv.ns][async_rv.rvid]
            return rv
        else:
            raise ValueError('Invalid return value id: "%s"'
                             % (async_rv.rvid,))

    def poll_rvs(self):
        """
        Returns list of Async_rv instances that are ready for reading.
        """
        rv = []
        for rvid, value in _g_async_rvs[self.ns].iteritems():
            if not isinstance(value, pythonshare.InProgress):
                rv.append(messages.Async_rv(self.ns, rvid))
        return rv

class Pythonshare_rns(object):
    """Remote namespace"""
    def __init__(self, conn, to_remote, from_remote):
        self.conn = conn
        self.to_remote = to_remote
        self.from_remote = from_remote
    def __del__(self):
        pythonshare._close(self.conn, self.to_remote, self.from_remote)

_g_local_namespaces = {}

# client-id -> set of namespaces
_g_namespace_users = {}
_g_executing_pythonshare_conn_id = None

# _g_remote_namespaces: namespace -> Connection to origin
_g_remote_namespaces = {}

# _g_namespace_exports: namespace -> list of Connections to which the
# namespace (remote or local) has been exported. If the namespace is
# deleted (or connection to origin is lost), these Connection objects
# are to be notified.
_g_namespace_exports = {}

_g_local_namespace_locks = {}
_g_async_rvs = {}
_g_async_rv_counter = 0

def _init_local_namespace(ns, init_code=None, force=False):
    if not ns in _g_local_namespaces:
        if opt_allow_new_namespaces or force:
            daemon_log('added local namespace "%s"' % (ns,))
            _g_local_namespaces[ns] = {
                "pythonshare_ns": Pythonshare_ns(ns),
                "Async_rv": pythonshare.messages.Async_rv
            }
            _g_local_namespace_locks[ns] = thread.allocate_lock()
            _g_async_rvs[ns] = {}
        else:
            raise ValueError('Unknown namespace "%s"' % (ns,))
    if init_code != None:
        try:
            exec init_code in _g_local_namespaces[ns]
        except Exception, e:
            daemon_log('namespace "%s" init error in <string>:\n%s\n\n%s' % (
                ns, code2string(init_code), exception2string(sys.exc_info())))

def _init_remote_namespace(ns, conn, to_remote, from_remote):
    if ns in _g_remote_namespaces:
        raise ValueError('Remote namespace "%s" already registered' % (
            ns,))
    daemon_log('added remote namespace "%s", origin "%s"' % (
        ns, conn.getpeername()))
    _g_remote_namespaces[ns] = Pythonshare_rns(conn, to_remote, from_remote)

def _register_exported_namespace(ns, conn):
    if not ns in _g_namespace_exports:
        _g_namespace_exports[ns] = []
    _g_namespace_exports[ns].append(conn)

def _local_execute(exec_msg, conn_id=None):
    global _g_executing_pythonshare_conn_id
    ns = exec_msg.namespace
    if conn_id:
        if not conn_id in _g_namespace_users:
            _g_namespace_users[conn_id] = set([ns])
        else:
            _g_namespace_users[conn_id].add(ns)
    code_exc, expr_exc, expr_rv = None, None, None
    if not exec_msg.lock or _g_local_namespace_locks[ns].acquire():
        _g_executing_pythonshare_conn_id = conn_id
        try:
            if exec_msg.code not in [None, ""]:
                try:
                    exec exec_msg.code in _g_local_namespaces[ns]
                except Exception, e:
                    code_exc = exception2string(sys.exc_info())
            if exec_msg.expr not in [None, ""]:
                try:
                    expr_rv = eval(exec_msg.expr, _g_local_namespaces[ns])
                except Exception, e:
                    expr_exc = exception2string(sys.exc_info())
        finally:
            _g_executing_pythonshare_conn_id = None
            if exec_msg.lock:
                _g_local_namespace_locks[ns].release()
    else:
        code_exc = expr_exc = 'locking namespace "%s" failed' % (ns,)
    if isinstance(expr_rv, pythonshare.messages.Exec_rv):
        return expr_rv
    else:
        return messages.Exec_rv(code_exc, expr_exc, expr_rv)

def _local_async_execute(async_rv, exec_msg):
    exec_rv = _local_execute(exec_msg)
    _g_async_rvs[exec_msg.namespace][async_rv.rvid] = exec_rv

def _remote_execute(ns, exec_msg):
    rns = _g_remote_namespaces[ns]
    cPickle.dump(exec_msg, rns.to_remote)
    rns.to_remote.flush()
    return cPickle.load(rns.from_remote)

def _remote_close(ns):
    del _g_remote_namespaces[ns]

def _connection_lost(conn_id, *closables):
    if closables:
        pythonshare._close(*closables)
    for ns in _g_namespace_users[conn_id]:
        _g_local_namespaces[ns]["pythonshare_ns"].call_on_disconnect(conn_id)

def _serve_connection(conn, conn_opts):
    global _g_async_rv_counter
    if isinstance(conn, client.Connection):
        to_client = conn._to_server
        from_client = conn._from_server
    else: # conn is a connected socket
        to_client = conn.makefile("w")
        from_client = conn.makefile("r")
    if opt_debug:
        daemon_log("connected %s:%s" % conn.getpeername())
    conn_id = "%s-%s" % (timestamp(), id(conn))
    auth_ok = False
    passwords = [k for k in conn_opts.keys() if k.startswith("password.")]
    if passwords:
        # password authentication is required for this connection
        received_password = cPickle.load(from_client)
        for password_type in passwords:
            algorithm = password_type.split(".")[1]
            if type(received_password) == str:
                if (algorithm == "plaintext" and
                    received_password == conn_opts[password_type]):
                    auth_ok = True
                elif (hasattr(hashlib, algorithm) and
                      getattr(hashlib, algorithm)(received_password).hexdigest() ==
                      conn_opts[password_type]):
                    auth_ok = True
        if auth_ok:
            cPickle.dump(messages.Auth_rv(True), to_client)
            if opt_debug:
                daemon_log("%s:%s authentication ok" % conn.getpeername())
        else:
            cPickle.dump(messages.Auth_rv(False), to_client)
            if opt_debug:
                daemon_log("%s:%s authentication failed" % conn.getpeername())
        to_client.flush()
    else:
       auth_ok = True # no password required

    while auth_ok:
        try:
            obj = cPickle.load(from_client)
            if opt_debug:
                daemon_log("%s:%s => %s" % (conn.getpeername() + (obj,)))
        except EOFError:
            break

        if isinstance(obj, messages.Register_ns):
            try:
                _init_remote_namespace(obj.ns, conn, to_client, from_client)
                cPickle.dump(messages.Ns_rv(True), to_client)
                to_client.flush()
                # from this point on, this connection is reserved for
                # sending remote namespace traffic. The connection will be
                # used by other threads, this thread stops here.
                return
            except Exception, e:
                cPickle.dump(messages.Ns_rv(False, exception2string(sys.exc_info())), to_client)
                to_client.flush()

        elif isinstance(obj, messages.Request_ns):
            ns = obj.ns
            if (ns in _g_remote_namespaces or
                ns in _g_local_namespaces):
                _register_exported_namespace(ns, conn)
                cPickle.dump(messages.Ns_rv(True), to_client)
                to_client.flush()
                # from this point on, this connection is reserved for
                # receiving executions on requested namespace. This
                # thread starts serving the connection.

        elif isinstance(obj, messages.Exec):
            ns = obj.namespace
            if ns in _g_remote_namespaces: # execute in remote namespace
                try:
                    exec_rv = _remote_execute(ns, obj)
                except EOFError: # connection lost
                    _remote_close(ns)
                    break
            else: # execute in local namespace
                _init_local_namespace(ns)
                if obj.async:
                    # asynchronous execution, return handle (Async_rv)
                    _g_async_rv_counter += 1
                    rvid = datetime.datetime.now().strftime(
                        "%s.%f") + str(_g_async_rv_counter)
                    exec_rv = messages.Async_rv(ns, rvid)
                    _g_async_rvs[ns][rvid] = pythonshare.InProgress()
                    thread.start_new_thread(_local_async_execute, (exec_rv, obj))
                else:
                    # synchronous execution, return true return value
                    exec_rv = _local_execute(obj, conn_id)
            if opt_debug:
                daemon_log("%s:%s <= %s" % (conn.getpeername() + (exec_rv,)))
            try:
                cPickle.dump(exec_rv, to_client)
            except (TypeError, ValueError, cPickle.PicklingError): # pickling rv fails
                exec_rv.expr_rv = messages.Unpicklable(exec_rv.expr_rv)
                cPickle.dump(exec_rv, to_client)
            to_client.flush()
        else:
            daemon_log("unknown message type: %s in %s" % (type(obj), obj))
            cPickle.dump(messages.Auth_rv(False), to_client)
            to_client.flush()
            auth_ok = False
    if opt_debug:
        daemon_log("disconnected %s:%s" % conn.getpeername())
    _connection_lost(conn_id, to_client, from_client, conn)

def start_server(host, port,
                 ns_init_import_export=[],
                 conn_opts={}):
    daemon_log("pid: %s" % (os.getpid(),))

    # Initialise, import and export namespaces
    for task, ns, arg in ns_init_import_export:
        if task == "init":
            _init_local_namespace(ns, arg, force=True)

        elif task == "export":
            _init_local_namespace(ns, None, force=True)
            c = pythonshare.connection(arg)
            if c.export_ns(ns):
                _register_exported_namespace(ns, c)
                thread.start_new_thread(_serve_connection, (c, {}))
            else:
                raise ValueError('Export namespace "%s" to "%s" failed'
                                 % (ns, arg))
        elif task == "import":
            if (ns in _g_local_namespaces or
                ns in _g_remote_namespaces):
                raise ValueError('Import failed, namespace "%s" already exists'
                                 % (ns,))
            c = pythonshare.connection(arg)
            if c.import_ns(ns):
                _init_remote_namespace(ns, c, c._to_server, c._from_server)

    try:
        addrinfos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        for addrinfo in addrinfos:
            daemon_log("listen: %s:%s" % (addrinfo[4][0], addrinfo[4][1]))
    except socket.error:
        daemon_log("listen: %s:%s" % (host, port))

    if isinstance(port, int):
        # Start listening to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if not on_windows:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(4)
        while 1:
            conn, _ = s.accept()
            thread.start_new_thread(_serve_connection, (conn, conn_opts))
    elif port == "stdin":
        opt_debug_stdout_limit = 0
        conn = client.Connection(sys.stdin, sys.stdout)
        _serve_connection(conn, conn_opts)

def start_daemon(host="localhost", port=8089, debug=False,
                 log_fd=None, ns_init_import_export=[], conn_opts={},
                 debug_stdout_limit=None):
    global opt_log_fd, opt_debug, opt_debug_stdout_limit
    opt_log_fd = log_fd
    opt_debug = debug
    if debug_stdout_limit != None:
        opt_debug_stdout_limit = debug_stdout_limit
    if opt_debug == False and not on_windows and isinstance(port, int):
        # The usual fork magic, cleaning up all connections to the parent process
        if os.fork() > 0:
            return
        os.chdir("/")
        os.umask(0)
        os.setsid()

        if os.fork() > 0:
            sys.exit(0)
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except (IOError, ValueError):
            pass

        daemon_output_file = "/dev/null"

        _in = file("/dev/null", 'r')
        _out = file(daemon_output_file, 'a+')
        _err = file(daemon_output_file, 'a+', 0)
        os.dup2(_in.fileno(), sys.stdin.fileno())
        os.dup2(_out.fileno(), sys.stdout.fileno())
        os.dup2(_err.fileno(), sys.stderr.fileno())

        dont_close = set([sys.stdin.fileno(),
                          sys.stdout.fileno(),
                          sys.stderr.fileno(),
                          log_fd])
        for fd in [int(s) for s in os.listdir("/proc/self/fd")]:
            if not fd in dont_close:
                try:
                    os.close(fd)
                except OSError:
                    pass

    start_server(host, port, ns_init_import_export, conn_opts)
