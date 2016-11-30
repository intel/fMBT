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

import client
import cPickle
import server
import messages
import socket
import subprocess
import urlparse as _urlparse
import thread

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
        if a in _send.locks:
            del _send.locks[a]
        if a in _recv.locks:
            del _recv.locks[a]
        if a:
            try:
                a.close()
            except (socket.error, IOError):
                pass

def _send(msg, destination):
    if not destination in _send.locks:
        _send.locks[destination] = thread.allocate_lock()
    with _send.locks[destination]:
        cPickle.dump(msg, destination, 2)
        destination.flush()
_send.locks = {}

def _recv(source):
    if not source in _recv.locks:
        _recv.locks[source] = thread.allocate_lock()
    with _recv.locks[source]:
        try:
            return cPickle.load(source)
        except (ValueError, cPickle.UnpicklingError), e:
            return messages.Unloadable(str(e))
        except EOFError:
            raise
        except Exception, e:
            return messages.Unloadable("load error %s: %s" % (type(e).__name__, e))
_recv.locks = {}

_g_hooks = {}

def _check_hook(signature, context):
    """Check if callbacks have been registered for a signature.
    If so, call them with the context"""
    if _g_hooks and signature in _g_hooks:
        for callback in _g_hooks[signature]:
            callback(signature, context)

def hook(event, callback):
    """Call callback function with traceback when event occurs.

    Parameters:

      event (string):
              supported event signatures:
              "before:client.socket.connect",
              "before:client.socket.close",
              "before:client.exec_in"

      callback (function):
              function that takes at least two parameters:
              signature and context.
    """
    if event in _g_hooks:
        _g_hooks[event].append(callback)
    else:
        _g_hooks[event] = [callback]

def connect(hostspec, password=None, namespace=None):
    """Returns Connection to pythonshare server at hostspec.

    Parameters:

      hostspec (string):
              Syntax:
              [socket://][PASSWORD@]HOST[:PORT][/NAMESPACE]
              shell://[SHELLCOMMAND]
              The default scheme is socket. Examples:
              hostname equals socket://hostname:8089
              host:port equals socket://host:port
              host/namespace equals socket://host:8089/namespace

      password (string, optional):
              use password to log in to the server. Overrides
              hostspec password.

      namespace (string, optional):
              send code to the namespace on server by default.
              Overrides hostspec namespace.
    """
    if not "://" in hostspec:
        hostspec = "socket://" + hostspec
    scheme, netloc, path, _, _ = _urlparse.urlsplit(hostspec)

    kwargs = {}
    if namespace != None:
        kwargs["namespace"] = namespace

    if scheme == "socket":
        # Parse URL
        if "@" in netloc:
            userinfo, hostport = netloc.split("@", 1)
        else:
            userinfo, hostport = "", netloc
        if ":" in userinfo:
            userinfo_user, userinfo_password = userinfo.split(":", 1)
        else:
            userinfo_user, userinfo_password = userinfo, None
        if ":" in hostport:
            host, port = hostport.split(":")
        else:
            host, port = hostport, default_port

        # If userinfo has been given, authenticate using it.
        # Allow forms
        # socket://password@host:port
        # socket://dontcare:password@host:port
        if password == None and userinfo:
            if userinfo_password:
                password = userinfo_password
            else:
                password = userinfo

        if not "namespace" in kwargs and path.replace("/", "", 1):
            kwargs["namespace"] = path.replace("/", "", 1)

        rv = client.Connection(host, int(port), password=password, **kwargs)
    elif scheme == "shell":
        p = subprocess.Popen(hostspec[len("shell://"):],
                             shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        rv = client.Connection(p.stdout, p.stdin, **kwargs)
    else:
        raise ValueError('invalid URI "%s"' % (hostspec,))
    rv.hostspec = hostspec
    return rv

def connection(*args, **kwargs):
    """DEPRECATED, use connect instead."""
    return connect(*args, **kwargs)
