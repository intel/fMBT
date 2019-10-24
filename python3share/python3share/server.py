# fMBT, free Model Based Testing tool
# Copyright (c) 2013-2017, Intel Corporation.
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

# pylint: disable=C0103,C0111,C0301,R0201,R0903,W0122,W0212,W0703

import pickle
import datetime
import getopt
import hashlib
import os
import platform
import socket
import sys
import tempfile
import _thread
import traceback
import urllib.parse
import python3share
import queue

messages = python3share.messages
client = python3share.client

on_windows = (os.name == "nt")
has_os_fdatasync = hasattr(os, "fdatasync")

opt_debug = False
opt_debug_limit = 240
opt_log_fd = None
opt_allow_new_namespaces = True

_g_wake_server_function = None
_g_waker_lock = None

def timestamp():
    if on_windows:
        rv = "%.6f" % (
            (datetime.datetime.utcnow() -
             datetime.datetime(1970, 1, 1)).total_seconds(),)
    else:
        rv = datetime.datetime.now().strftime("%s.%f")
    return rv

def daemon_log(msg):
    if opt_debug_limit >= 0:
        if len(msg) > opt_debug_limit:
            msg = (msg[:opt_debug_limit//2] +
                   ("...[%s B, log CRC %s]..." % (len(msg), messages.crc(msg))) +
                   msg[-opt_debug_limit//2:])
    formatted_msg = "%s %s\n" % (timestamp(), msg)
    if opt_log_fd != None:
        os.write(opt_log_fd, str.encode(formatted_msg))
        if has_os_fdatasync:
            os.fdatasync(opt_log_fd)
    if opt_debug and opt_debug_limit != 0:
        sys.stdout.write(formatted_msg)
        sys.stdout.flush()

def code2string(code):
    return "\n".join(
        ["%-4s %s" % (li+1, l) for li, l in enumerate(code.splitlines())])

def exception2string(exc_info):
    return ''.join(traceback.format_exception(*exc_info))

def _store_return_value(func, queue):
    while True:
        queue.put(func())

class Pythonshare_ns(object):
    """Pythonshare services inside a namespace
    """
    def __init__(self, ns):
        self.ns = ns
        self._on_disconnect = []
        self._on_drop = []

    def ns_type(self, ns):
        """Query the type of a namespace.

        Returns "local" or "remote" if namespace exists, otherwise None.
        """
        if ns in _g_local_namespaces:
            return "local"
        elif ns in _g_remote_namespaces:
            return "remote"
        else:
            return None

    def local_nss(self):
        """List local namespaces
        """
        return list(_g_local_namespaces.keys())

    def remote_nss(self, ls_opts={}):
        """List remote namespaces
        """
        if "ip" in ls_opts and ls_opts["ip"] == True:
            return {k: _g_remote_namespaces[k].conn.getpeername()
                    for k in _g_remote_namespaces.keys()}
        return list(_g_remote_namespaces.keys())

    def on_disconnect(self):
        """Return codes that will be executed when a client has disconnected.
        """
        return self._on_disconnect

    def on_drop(self):
        """Return codes that will be executed when the namespace is dropped.
        """
        return self._on_drop

    def exec_on_disconnect(self, code, any_connection=False):
        """Add code that will be executed when client has disconnected.
        """
        if not any_connection:
            conn_id = _g_executing_pythonshare_conn_id
        else:
            conn_id = None
        self._on_disconnect.append((conn_id, code))

    def exec_on_drop(self, code):
        """Add code that will be executed when namespace is dropped.
        """
        self._on_drop.append(code)

    def set_on_disconnect(self, list_of_code):
        """Replace all "on disconnect" codes with new list of codes.
        """
        self._on_disconnect = list_of_code

    def set_on_drop(self, list_of_code):
        """Replace all "on drop" codes with new list of codes."""
        self._on_drop = list_of_code

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

    def call_on_drop(self):
        for code in self._on_drop:
            exec_msg = messages.Exec(self.ns, code, None)
            if opt_debug:
                daemon_log("on drop: %s" % (exec_msg,))
            rv = _local_execute(exec_msg)
            if opt_debug:
                daemon_log("on drop rv: %s" % (rv,))

    def read_rv(self, async_rv):
        """Return and remove asynchronous return value.
        """
        if self.ns != async_rv.ns:
            raise ValueError("Namespace mismatch")
        if (async_rv.ns in _g_async_rvs and
            async_rv.rvid in _g_async_rvs[async_rv.ns]):
            rv = _g_async_rvs[async_rv.ns][async_rv.rvid]
            if not isinstance(rv, python3share.InProgress):
                del _g_async_rvs[async_rv.ns][async_rv.rvid]
            return rv
        else:
            raise ValueError('Invalid return value id: "%s"'
                             % (async_rv.rvid,))

    def poll_rvs(self):
        """Returns list of Async_rv instances that are ready for reading.
        """
        rv = []
        for rvid, value in _g_async_rvs[self.ns].items():
            if not isinstance(value, python3share.InProgress):
                rv.append(messages.Async_rv(self.ns, rvid))
        return rv

class Pythonshare_rns(object):
    """Remote namespace"""
    def __init__(self, conn, to_remote, from_remote):
        self.conn = conn
        self.to_remote = to_remote
        self.from_remote = from_remote
    def __del__(self):
        python3share._close(self.conn, self.to_remote, self.from_remote)

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
_g_server_shutdown = False

def _init_local_namespace(ns, init_code=None, force=False):
    if not ns in _g_local_namespaces:
        if opt_allow_new_namespaces or force:
            daemon_log('added local namespace "%s"' % (ns,))
            _g_local_namespaces[ns] = {
                "pythonshare_ns": Pythonshare_ns(ns),
                "Async_rv": python3share.messages.Async_rv
            }
            _g_local_namespace_locks[ns] = _thread.allocate_lock()
            _g_async_rvs[ns] = {}
        else:
            raise ValueError('Unknown namespace "%s"' % (ns,))
    if init_code != None:
        if isinstance(init_code, str):
            try:
                exec(init_code, _g_local_namespaces[ns])
            except Exception as e:
                daemon_log('namespace "%s" init error in <string>:\n%s\n\n%s' % (
                    ns, code2string(init_code), exception2string(sys.exc_info())))
        elif isinstance(init_code, dict):
            # Directly use the dictionary (locals() or globals(), for
            # instance) as a Pythonshare namespace.
            clean_ns = _g_local_namespaces[ns]
            _g_local_namespaces[ns] = init_code
            _g_local_namespaces[ns].update(clean_ns) # copy pythonshare defaults
        else:
            raise TypeError("unsupported init_code type")

def _drop_local_namespace(ns):
    daemon_log('drop local namespace "%s"' % (ns,))
    _g_local_namespaces[ns]["pythonshare_ns"].call_on_drop()
    del _g_local_namespaces[ns]
    del _g_local_namespace_locks[ns]
    del _g_async_rvs[ns]
    # send notification to all connections in _g_namespace_exports[ns]?

def _drop_remote_namespace(ns):
    daemon_log('drop remote namespace "%s"' % (ns,))
    try:
        rns = _g_remote_namespaces[ns]
        del _g_remote_namespaces[ns]
        rns.__del__()
    except KeyError:
        pass # already dropped
    # send notification to all connections in _g_namespace_exports[ns]?

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
    if not ns in _g_local_namespaces:
        code_exc = expr_exc = "no local namespace %s" % (ns,)
        return messages.Exec_rv(code_exc, expr_exc, None)
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
                    exec(exec_msg.code, _g_local_namespaces[ns])
                except Exception as e:
                    code_exc = exception2string(sys.exc_info())
            if exec_msg.expr not in [None, ""]:
                try:
                    expr_rv = eval(exec_msg.expr, _g_local_namespaces[ns])
                except Exception as e:
                    expr_exc = exception2string(sys.exc_info())
        finally:
            _g_executing_pythonshare_conn_id = None
            if exec_msg.lock:
                try:
                    _g_local_namespace_locks[ns].release()
                except _thread.error:
                    pass # already unlocked namespace
    else:
        code_exc = expr_exc = 'locking namespace "%s" failed' % (ns,)
    if isinstance(expr_rv, python3share.messages.Exec_rv):
        return expr_rv
    else:
        return messages.Exec_rv(code_exc, expr_exc, expr_rv)

def _local_async_execute(async_rv, exec_msg):
    exec_rv = _local_execute(exec_msg)
    _g_async_rvs[exec_msg.namespace][async_rv.rvid] = exec_rv

def _remote_execute(ns, exec_msg):
    rns = _g_remote_namespaces[ns]
    python3share._send(exec_msg, rns.to_remote)
    # _recv raises EOFError() if disconnected,
    # let it raise through.
    return python3share._recv(rns.from_remote)

def _remote_execute_and_forward(ns, exec_msg, to_client, peername=None):
    """returns (forward_status, info)
    forward_status values:
       True:  everything successfully forwarded,
              info contains pair (forwarded byte count, full length).
       False: not everything forwarded,
              info contains pair (forwarded byte count, full length).
              to_client file/socket is not functional.
       None:  no forwarding,
              info contains Exec_rv that should be sent normally.
    Raises EOFError if connection to remote namespace is not functional.

    The peername parameter is used for logging only.
    """
    client_supports_rv_info = exec_msg.recv_cap_data_info()
    exec_msg.set_recv_cap_data_info(True)
    rns = _g_remote_namespaces[ns]
    from_remote = rns.from_remote
    # Must keep simultaneously two locks:
    # - send lock on to_client
    # - recv lock on from_remote
    python3share._acquire_recv_lock(from_remote)
    try:
        python3share._send(exec_msg, rns.to_remote)
        response = python3share._recv(from_remote, acquire_recv_lock=False)
        if not isinstance(response, messages.Data_info):
            # Got direct response without forward mode
            return (None, response)
        python3share._acquire_send_lock(to_client)
        if client_supports_rv_info:
            # send data_info to client
            python3share._send(response, to_client, acquire_send_lock=False)
        try:
            if opt_debug and peername:
                daemon_log("%s:%s <= Exec_rv([forwarding %s B])" % (peername + (response.data_length,)))
            forwarded_bytes = python3share._forward(
                from_remote, to_client, response.data_length,
                acquire_recv_lock=False,
                acquire_send_lock=False)
            if forwarded_bytes == response.data_length:
                return (True, (forwarded_bytes, response.data_length))
            else:
                return (False, (forwarded_bytes, response.data_length))
        finally:
            python3share._release_send_lock(to_client)
    finally:
        exec_msg.set_recv_cap_data_info(client_supports_rv_info)
        python3share._release_recv_lock(from_remote)

def _connection_lost(conn_id, *closables):
    if closables:
        python3share._close(*closables)
    try:
        for ns in _g_namespace_users[conn_id]:
            try:
                _g_local_namespaces[ns]["pythonshare_ns"].call_on_disconnect(conn_id)
            except KeyError:
                pass
    except KeyError:
        pass

def _serve_connection(conn, conn_opts):
    global _g_async_rv_counter
    global _g_server_shutdown
    if isinstance(conn, client.Connection):
        to_client = conn._to_server
        from_client = conn._from_server
    else: # conn is a connected socket
        to_client = conn.makefile("wb")
        from_client = conn.makefile("rb")
    try:
        peername = conn.getpeername()
    except socket.error:
        peername = ("unknown", "?")
    if opt_debug:
        daemon_log("connected %s:%s" % peername)
    conn_id = "%s-%s" % (timestamp(), id(conn))
    auth_ok = False
    passwords = [k for k in conn_opts.keys() if k.startswith("password.")]
    kill_server_on_close = conn_opts.get("kill-server-on-close", False)
    if passwords:
        # password authentication is required for this connection
        try:
            received_password = python3share._recv(from_client)
        except Exception as e:
            daemon_log('error receiving password: %r' % (e,))
            received_password = None
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
        try:
            if auth_ok:
                python3share._send(messages.Auth_rv(True), to_client)
                if opt_debug:
                    daemon_log("%s:%s authentication ok" % peername)
            elif not received_password is None:
                python3share._send(messages.Auth_rv(False), to_client)
                if opt_debug:
                    daemon_log("%s:%s authentication failed" % peername)
        except socket.error:
            daemon_log("authentication failed due to socket error")
            auth_ok = False
    else:
        auth_ok = True # no password required

    whitelist_local = conn_opts.get("whitelist_local", None)

    while auth_ok:
        try:
            obj = python3share._recv(from_client)
            if opt_debug:
                daemon_log("%s:%s => %s" % (peername + (obj,)))
        except (EOFError, python3share.socket.error):
            break

        if isinstance(obj, messages.Register_ns):
            try:
                _init_remote_namespace(obj.ns, conn, to_client, from_client)
                python3share._send(messages.Ns_rv(True), to_client)
                # from this point on, this connection is reserved for
                # sending remote namespace traffic. The connection will be
                # used by other threads, this thread stops here.
                return
            except Exception as e:
                python3share._send(messages.Ns_rv(False, exception2string(sys.exc_info())), to_client)

        elif isinstance(obj, messages.Drop_ns):
            try:
                if obj.ns in _g_local_namespaces:
                    _drop_local_namespace(obj.ns)
                elif obj.ns in _g_remote_namespaces:
                    _drop_remote_namespace(obj.ns)
                else:
                    raise ValueError('Unknown namespace "%s"' % (obj.ns,))
                python3share._send(messages.Ns_rv(True), to_client)
            except Exception as e:
                if opt_debug:
                    daemon_log("namespace drop error: %s" % (e,))
                python3share._send(messages.Ns_rv(False, exception2string(sys.exc_info())), to_client)

        elif isinstance(obj, messages.Request_ns):
            ns = obj.ns
            if (ns in _g_remote_namespaces or
                ns in _g_local_namespaces):
                _register_exported_namespace(ns, conn)
                python3share._send(messages.Ns_rv(True), to_client)
                # from this point on, this connection is reserved for
                # receiving executions on requested namespace. This
                # thread starts serving the connection.

        elif isinstance(obj, messages.Exec):
            ns = obj.namespace
            if ns in _g_remote_namespaces: # execute in remote namespace
                try:
                    _fwd_status, _fwd_info = _remote_execute_and_forward(
                        ns, obj, to_client, peername)
                    if _fwd_status == True:
                        # successfully forwarded
                        if opt_debug:
                            daemon_log("%s:%s forwarded %s B" % (peername + (_fwd_info[0],)))
                        exec_rv = None # return value fully forwarded
                    elif _fwd_status == False:
                        # connection to client is broken
                        if opt_debug:
                            daemon_log("%s:%s error after forwarding %s/%s B" % (peername + _fwd_info))
                        break
                    elif _fwd_status is None:
                        # nothing forwarded, send return value by normal means
                        exec_rv = _fwd_info
                except EOFError:
                    daemon_log('connection lost to "%s"' % (ns,))
                    _drop_remote_namespace(ns)
                    break
            else: # execute in local namespace
                if whitelist_local == None or ns in whitelist_local:
                    _init_local_namespace(ns)
                if getattr(obj, "async"):
                    # asynchronous execution, return handle (Async_rv)
                    _g_async_rv_counter += 1
                    rvid = timestamp() + str(_g_async_rv_counter)
                    exec_rv = messages.Async_rv(ns, rvid)
                    _g_async_rvs[ns][rvid] = python3share.InProgress()
                    _thread.start_new_thread(_local_async_execute, (exec_rv, obj))
                else:
                    # synchronous execution, return true return value
                    exec_rv = _local_execute(obj, conn_id)
            if not exec_rv is None:
                if opt_debug:
                    daemon_log("%s:%s <= %s" % (peername + (exec_rv,)))
                try:
                    try:
                        if obj.recv_cap_data_info():
                            info = python3share._send_opt(exec_rv, to_client, obj.recv_caps)
                            if info:
                                sent_info = " %s B, format:%s" % (
                                    info.data_length, info.data_format)
                            else:
                                sent_info = ""
                        else:
                            python3share._send(exec_rv, to_client)
                            sent_info = ""
                        if opt_debug:
                            daemon_log("%s:%s sent%s" % (peername + (sent_info,)))
                    except (EOFError, socket.error):
                        break
                except (TypeError, ValueError, pickle.PicklingError): # pickling rv fails
                    exec_rv.expr_rv = messages.Unpicklable(exec_rv.expr_rv)
                    try:
                        python3share._send(exec_rv, to_client)
                    except (EOFError, socket.error):
                        break

        elif isinstance(obj, messages.Server_ctl):
            if obj.command == "die":
                ns = obj.args[0]
                if ns in _g_remote_namespaces:
                    try:
                        rv = _remote_execute(ns, obj)
                        if opt_debug:
                            daemon_log("%s:%s <= %s" % (peername + (rv,)))
                        python3share._send(rv, to_client)
                    except (EOFError, socket.error): # connection lost
                        daemon_log('connection lost to "%s"' % (ns,))
                        _drop_remote_namespace(ns)
                        break
                else:
                    _g_server_shutdown = True
                    server_ctl_rv = messages.Server_ctl_rv(0, "shutting down")
                    python3share._send(server_ctl_rv, to_client)
                    if _g_wake_server_function:
                        _g_wake_server_function()
                    break
            elif obj.command == "unlock":
                try:
                    ns = obj.args[0]
                    if ns in _g_remote_namespaces:
                        try:
                            rv = _remote_execute(ns, obj)
                        except (EOFError, socket.error): # connection lost
                            daemon_log('connection lost to "%s"' % (ns,))
                            _drop_remote_namespace(ns)
                            break
                    elif ns in _g_local_namespace_locks:
                        try:
                            _g_local_namespace_locks[ns].release()
                            server_ctl_rv = messages.Server_ctl_rv(
                                0, "%s unlocked" % (repr(ns),))
                        except _thread.error as e:
                            server_ctl_rv = messages.Server_ctl_rv(
                                1, "%s already unlocked" %
                                (repr(ns),))
                    elif ns in _g_local_namespaces:
                        server_ctl_rv = messages.Server_ctl_rv(
                            2, "namespace %s is not locked" % (repr(ns),))
                    else:
                        server_ctl_rv = messages.Server_ctl_rv(
                            -1, "unknown namespace %s" % (repr(ns),))
                    if opt_debug:
                        daemon_log("%s:%s <= %s" % (peername + (server_ctl_rv,)))
                    python3share._send(server_ctl_rv, to_client)
                except Exception as e:
                    if opt_debug:
                        daemon_log("Exception in handling %s: %s" % (obj, e))
        else:
            daemon_log("unknown message type: %s in %s" % (type(obj), obj))
            python3share._send(messages.Auth_rv(False), to_client)
            auth_ok = False
    if opt_debug:
        daemon_log("disconnected %s:%s" % peername)
    _connection_lost(conn_id, to_client, from_client, conn)
    if kill_server_on_close:
        _g_server_shutdown = True
        if _g_wake_server_function:
            _g_wake_server_function()

def start_server(host, port,
                 ns_init_import_export=[],
                 conn_opts={},
                 listen_stdin=True):
    global _g_wake_server_function
    global _g_waker_lock
    daemon_log("pid: %s" % (os.getpid(),))

    # Initialise, import and export namespaces
    for task, ns, arg in ns_init_import_export:
        if task == "init":
            # If arg is a string, it will be executed in ns.
            # If arg is a dict, it will be used as ns.
            _init_local_namespace(ns, arg, force=True)

        elif task == "export":
            # Make sure ns exists before exporting.
            _init_local_namespace(ns, None, force=True)
            daemon_log('exporting "%s" to %s' % (ns, arg))
            try:
                c = python3share.connection(arg)
            except Exception as e:
                daemon_log('connecting to %s failed: %s' % (arg, e))
                return
            if c.export_ns(ns):
                _register_exported_namespace(ns, c)
                _thread.start_new_thread(
                    _serve_connection, (c, {"kill-server-on-close": True}))
            else:
                raise ValueError('Export namespace "%s" to "%s" failed'
                                 % (ns, arg))
        elif task == "import":
            if (ns in _g_local_namespaces or
                ns in _g_remote_namespaces):
                raise ValueError('Import failed, namespace "%s" already exists'
                                 % (ns,))
            c = python3share.connection(arg)
            if c.import_ns(ns):
                _init_remote_namespace(ns, c, c._to_server, c._from_server)

    try:
        addrinfos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        for addrinfo in addrinfos:
            daemon_log("listen: %s:%s" % (addrinfo[4][0], addrinfo[4][1]))
    except socket.error:
        daemon_log("listen: %s:%s" % (host, port))

    if isinstance(port, int):
        def wake_server_function():
            _g_waker_lock.release() # wake up server
        _g_wake_server_function = wake_server_function
        _g_waker_lock = _thread.allocate_lock()
        _g_waker_lock.acquire() # unlocked

        # Start listening to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except:
            pass
        s.bind((host, port))
        s.listen(4)
        event_queue = queue.Queue()
        _thread.start_new_thread(_store_return_value, (s.accept, event_queue))
        _thread.start_new_thread(_store_return_value, (_g_waker_lock.acquire, event_queue))
        if not sys.stdin.closed and listen_stdin:
            daemon_log("listening to stdin")
            _thread.start_new_thread(_store_return_value, (sys.stdin.readline, event_queue))
        else:
            daemon_log("not listening stdin")
        while 1:
            event = event_queue.get()
            if isinstance(event, tuple):
                # returned from s.accept
                conn, _ = event
                _thread.start_new_thread(_serve_connection, (conn, conn_opts))
            elif event == True:
                # returned from _g_waker_lock.acquire
                daemon_log("shutting down.")
                break
            else:
                # returned from sys.stdin.readline
                pass
    elif port == "stdin":
        opt_debug_limit = 0
        if os.name == "nt":
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        conn = client.Connection(sys.stdin, sys.stdout)
        _serve_connection(conn, conn_opts)
    for ns in sorted(_g_remote_namespaces.keys()):
        _drop_remote_namespace(ns)
    for ns in sorted(_g_local_namespaces.keys()):
        _drop_local_namespace(ns)

def start_daemon(host="localhost", port=8089, debug=False,
                 log_fd=None, ns_init_import_export=[], conn_opts={},
                 debug_limit=None):
    global opt_log_fd, opt_debug, opt_debug_limit
    opt_log_fd = log_fd
    opt_debug = debug
    if debug_limit != None:
        opt_debug_limit = debug_limit
    if opt_debug_limit > 0:
        messages.MSG_STRING_FIELD_MAX_LEN = max(opt_debug_limit//3-40, 40)
    else:
        messages.MSG_STRING_FIELD_MAX_LEN = None
    if opt_debug == False and not on_windows and isinstance(port, int):
        listen_stdin = False
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

        _in = open("/dev/null", 'r')
        _out = open(daemon_output_file, 'a+')
        _err = open(daemon_output_file, 'a+b', 0)
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
    else:
        listen_stdin = True

    start_server(host, port, ns_init_import_export, conn_opts, listen_stdin)
