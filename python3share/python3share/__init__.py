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

import ast
from . import client
import pickle
from . import server
from . import messages
import os
import socket
import subprocess
import urllib.parse as _urlparse
import time
import _thread
import zlib

from .messages import Exec, Exec_rv

try:
    _PYTHONSHARE_HOSTSPECS = ast.literal_eval(
        os.getenv("PYTHONSHARE_HOSTSPECS", "{}"))
except Exception:
    _PYTHONSHARE_HOSTSPECS = {}

# Minimum string length for optimized sending
_SEND_OPT_MESSAGE_MIN = 1024*128    # optimize sending msgs of at least 128 kB
_SEND_OPT_BLOCK_SIZE = 1024*64      # flush between 64 kB blocks when sending
_SEND_OPT_COMPRESS_TRIAL = 1024*128 # size of compress test block
_SEND_OPT_COMPRESS_MIN = 0.8        # compress at least 0.8 * orig or smaller
_SEND_OPT_COMPRESSION_LEVEL = 3     # zlib compression level, speed over size

# Connection = client.Connection
default_port = 8089 # str(ord("P")) + str(ord("Y"))

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
        if a:
            try:
                a.close()
            except (socket.error, IOError):
                pass
        if a in _send.locks:
            try:
                while _send.locks[a].locked():
                    _send.locks[a].release()
                    time.sleep(0.1)
            except:
                pass
            del _send.locks[a]
        if a in _recv.locks:
            try:
                while _recv.locks[a].locked():
                    _recv.locks[a].release()
                    time.sleep(0.1)
            except:
                pass
            del _recv.locks[a]

def _send(msg, destination, acquire_send_lock=True, pickle_=True):
    if acquire_send_lock:
        _acquire_send_lock(destination)
    try:
        if pickle_:
            pickle.dump(msg, destination, 2)
        else:
            destination.write(msg)
        destination.flush()
    finally:
        if acquire_send_lock:
            _release_send_lock(destination)
_send.locks = {}

def _send_opt(msg, destination, recv_caps, acquire_send_lock=True):
    data = pickle.dumps(msg, 2)
    data_length = len(data)
    if data_length < _SEND_OPT_MESSAGE_MIN:
        _send(data, destination, acquire_send_lock=acquire_send_lock, pickle_=False)
        return None
    if recv_caps & messages.RECV_CAP_COMPRESSION:
        # Try if compressing makes sense. For instance, at least 20 %
        # compression could be required for the first block to compress
        # everything.
        compress_block_len = min(data_length, _SEND_OPT_COMPRESS_TRIAL)
        compressed_block = zlib.compress(data[:compress_block_len],
                                         _SEND_OPT_COMPRESSION_LEVEL)
        if len(compressed_block) < compress_block_len * _SEND_OPT_COMPRESS_MIN:
            _uncompressed_data_length = data_length
            if compress_block_len == data_length:
                # everything got compressed for trial
                data = compressed_block
            else:
                # only first bytes were compressed in trial, compress all now
                data = zlib.compress(data, _SEND_OPT_COMPRESSION_LEVEL)
            data_length = len(data)
            compression_info = "compressed(%s)" % (_uncompressed_data_length,)
        else:
            compression_info = "no_compression"
    else:
        compression_info = "no_compression"
    data_info = messages.Data_info(
        data_type="Exec_rv",
        data_length=data_length,
        data_format=compression_info + ",pickled,allinone")
    if acquire_send_lock:
        _acquire_send_lock(destination)
    try:
        send_delay = float(os.getenv("PYTHONSHARE_SEND_DELAY","0.0"))
    except:
        send_delay = 0.0
    try:
        _send(data_info, destination, acquire_send_lock=False)
        bytes_sent = 0
        while bytes_sent < data_length:
            block_len = min(_SEND_OPT_BLOCK_SIZE, data_length-bytes_sent)
            data_block = data[bytes_sent:bytes_sent+block_len]
            # this may raise socket.error, let it raise through
            destination.write(data_block)
            if send_delay > 0.0:
                time.sleep(send_delay)
            destination.flush()
            bytes_sent += block_len
    finally:
        _release_send_lock(destination)
    return data_info

def _recv(source, acquire_recv_lock=True):
    """returns the first message from source"""
    if acquire_recv_lock:
        _acquire_recv_lock(source)
    try:
        try:
            return pickle.load(source)
        except (ValueError, pickle.UnpicklingError) as e:
            return messages.Unloadable(str(e))
        except EOFError:
            raise
        except socket.error as e:
            raise EOFError("socket.error: " + str(e))
        except AttributeError as e:
            # If another thread closes the connection between send/recv,
            # cPickle.load() may raise "'NoneType' has no attribute 'recv'".
            # Make this look like EOF (connection lost)
            raise EOFError(str(e))
        except Exception as e:
            return messages.Unloadable("load error %s: %s" % (type(e).__name__, e))
    finally:
        if acquire_recv_lock:
            _release_recv_lock(source)
_recv.locks = {}

def _recv_with_info(source, acquire_recv_lock=True):
    """returns the first payload message from source that may/may not be
    preceded by Data_info
    """
    if acquire_recv_lock:
        _acquire_recv_lock(source)
    try:
        msg = _recv(source, False)
        if not isinstance(msg, messages.Data_info):
            return msg
        data = source.read(msg.data_length)
        if len(data) != msg.data_length:
            raise EOFError()
        if "compressed(" in msg.data_format:
            data = zlib.decompress(data)
        try:
            return pickle.loads(data)
        except (ValueError, pickle.UnpicklingError) as e:
            return messages.Unloadable(str(e))
        except Exception as e:
            return messages.Unloadable("load error %s: %s" % (type(e).__name__, e))
    finally:
        if acquire_recv_lock:
            _release_recv_lock(source)

def _forward(source, destination, data_length,
             acquire_send_lock=True,
             acquire_recv_lock=True):
    if acquire_recv_lock:
        _acquire_recv_lock(source)
    if acquire_send_lock:
        _acquire_send_lock(destination)
    destination_ok = True
    try:
        bytes_sent = 0
        bytes_read = 0
        forward_block_size = _SEND_OPT_BLOCK_SIZE
        while bytes_read < data_length:
            forward_block = source.read(
                min(forward_block_size, data_length - bytes_read))
            bytes_read += len(forward_block)
            if forward_block:
                if destination_ok:
                    try:
                        destination.write(forward_block)
                        destination.flush()
                        bytes_sent += len(forward_block)
                    except socket.error:
                        destination_ok = False
                        # must still keep reading everything from the source
            else:
                raise EOFError() # source run out of data
        return bytes_sent
    finally:
        if acquire_recv_lock:
            _release_recv_lock(source)
        if acquire_send_lock:
            _release_send_lock(destination)

def _acquire_recv_lock(source):
    if not source in _recv.locks:
        _recv.locks[source] = _thread.allocate_lock()
    _recv.locks[source].acquire()

def _acquire_send_lock(destination):
    if not destination in _send.locks:
        _send.locks[destination] = _thread.allocate_lock()
    _send.locks[destination].acquire()

def _release_recv_lock(source):
    try:
        _recv.locks[source].release()
    except _thread.error:
        pass # already released

def _release_send_lock(destination):
    try:
        _send.locks[destination].release()
    except _thread.error:
        pass # already released

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
              hostspec can also be a key in PYTHONSHARE_HOSTSPECS
              environment variable (a Python dictionary that maps
              shorthands to real hostspecs).

      password (string, optional):
              use password to log in to the server. Overrides
              hostspec password.

      namespace (string, optional):
              send code to the namespace on server by default.
              Overrides hostspec namespace.
    """
    if hostspec in _PYTHONSHARE_HOSTSPECS:
        hostspec = _PYTHONSHARE_HOSTSPECS[hostspec]
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
        if os.name == "nt":
            import msvcrt
            msvcrt.setmode(p.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(p.stdout.fileno(), os.O_BINARY)
        rv = client.Connection(p.stdout, p.stdin, **kwargs)
    else:
        raise ValueError('invalid URI "%s"' % (hostspec,))
    rv.hostspec = hostspec
    return rv

def connection(*args, **kwargs):
    """DEPRECATED, use connect instead."""
    return connect(*args, **kwargs)
