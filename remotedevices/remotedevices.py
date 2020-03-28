# fMBT, free Model Based Testing tool
# Copyright (c) Intel Corporation.
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

"""Acquire and release devices hosted by remotedevices-server

Example 1: acquire and release a Device object

import remotedevices
d = remotedevices.acquireDevice("server:port", type="android")
d.refreshScreenshot() # d is fmbtandroid.Device instance
d.swipeBitmap("lockscreen-lock.png", "west")
remotedevices.releaseDevice(d)

Example 2: acquire and release a Connection object

* use environment variables:
  REMOTEDEVICES_SERVER=password@server:port
  (avoids hardcoding them to the code)

* use display match expression to acquire a device with specific
  display dimensions

import fmbtandroid
import remotedevices
d = fmbtandroid.Device(connect=False)
d.setConnection(remotedevices.acquireConnection(type="android", display="480x800"))
if not d.connection():
    print "failed to connect"
else:
    print "got device:", d.serialNumber
    remotedevices.releaseConnection(d.connection())
    d.setConnection(None)
"""

import fmbtandroid
import pythonshare
import os
import socket

connectionDeviceTypes = ["android"]

class Proxy:
    def __init__(self, serialNumber, pythonshareConnectionNamespace):
        self._id = serialNumber
        self._serialNumber = serialNumber
        self._ps_conn = pythonshareConnectionNamespace[0]
        self._ps_ns = pythonshareConnectionNamespace[1]

    def __eq__(self, obj):
        return id(self) == id(obj)

    def __ne__(self, obj):
        return not self == obj

    def __nonzero__(self):
        return True

    def __repr__(self):
        return str(self)

    def _remoteEval(self, pythonCode):
        return self._ps_conn.eval_in(self._ps_ns, pythonCode, lock=False)

class ConnectionProxy(Proxy):
    def __init__(self, serialNumber, pythonshareConnectionNamespace):
        Proxy.__init__(self, serialNumber, pythonshareConnectionNamespace)
        self._serialNumber = serialNumber

    def __getattr__(self, attrname):
        try:
            self._ps_conn.eval_in(self._ps_ns, "devices.acquired(%s).connection().%s" % (repr(self._id), attrname))
        except pythonshare.RemoteEvalError, e:
            raise AttributeError(e)

    def __str__(self):
        return "ConnectionProxy(%s)" % (repr(self._ps_conn),)

    def _forwardCall(self, methodName, *args, **kwargs):
        arg_list = ([repr(a) for a in args] +
                    ['%s=%s' % (k, repr(v)) for k, v in kwargs.iteritems()])
        return self._remoteEval(
            "devices.acquired(%s).connection().%s(%s)" % (
            repr(self._id), methodName, ", ".join(arg_list)))

    def recvScreenshot(self, filename):
        remoteFilename = os.path.join("/tmp", os.path.basename(filename))
        if self._forwardCall("recvScreenshot", remoteFilename) != True:
            return False
        file(filename, "wb").write(
            self._remoteEval('file("%s", "rb").read()' % (remoteFilename,)))
        self._remoteEval('os.remove("%s")' % (remoteFilename,))
        return True

# Most methods are fine with a simple proxy
def _methodProxy(methodName):
    return (lambda self, *args, **kwargs:
            self._forwardCall(methodName, *args, **kwargs))

for m in dir(fmbtandroid._AndroidDeviceConnection):
    if getattr(ConnectionProxy, m, None) == None and (
            m.startswith("send") or
            m.startswith("recv") or
            m.startswith("set") or
            m in ["_runAdb", "reboot", "shellSOE",  "target", "settings",
                  "screencapArgs"]):
        setattr(ConnectionProxy, m, _methodProxy(m))

class GenericProxy(Proxy):
    """proxy all attributes as methods"""
    def __init__(self, id, pythonshareConnectionNamespace):
        Proxy.__init__(self, id, pythonshareConnectionNamespace)

    def __str__(self):
        return "GenericProxy(%s, %s)" % (
            repr(self._id), repr((self._ps_conn, self._ps_ns)))

    def __dir__(self):
        return self._remoteEval(
            "[a for a in dir(devices.acquired(%s))"
            " if callable(getattr(devices.acquired(%s), a))]" % (
                repr(self._id), repr(self._id)))

    def _remoteCall(self, method, args, kwargs):
        return self._remoteEval(
            "devices.acquired(%s).%s(%s)" % (
                repr(self._id),
                method,
                ",".join([repr(a) for a in args] +
                         ["%s=%s" % (k, repr(kwargs[k])) for k in kwargs])))

    def __getattr__(self, attrname):
        return lambda *args, **kwargs: self._remoteCall(attrname, args, kwargs)

def acquire(pythonshareHostspec=None, block=True, acquirer=None,
            **matchRegexps):
    """Acquire a remote object.

    Parameters:

      pythonshareHostSpec (string, optional):
              [password@]host[:port] of pythonshare-server that hosts
              remotedevices-server. If not given, environment variable
              REMOTEDEVICES_SERVER will be used. If that is undefined,
              "localhost" will be used.

      block (boolean, optional):
              If True, call is blocked until a matching device is acquired.
              Otherwise, the call will return None in case any of the matching
              devices could not be acquired.

      acquirer (string, optional):
              Acquirer id. The default is REMOTEDEVICES_ACQID or an
              empty string.

      property=regexp (optional):
              Requirements for the object. Examples:
              o = acquire(type="example-lightbulb")
              o = acquire(id=".*-lightbulb-[0-9]")

    Returns a proxy that forwards all method calls to acquired remote object.
    The object must be released with release(proxy).

    Note: use acquireDevice to create local fMBT GUI test interface
    objects that use remote GUITestConnection to access remote device.
    """
    serialNumber, ps_conn, ps_ns = _acquire(pythonshareHostspec, block,
                                            acquirer=acquirer, **matchRegexps)
    if serialNumber == None:
        return None
    else:
        return GenericProxy(serialNumber, (ps_conn, ps_ns))

def release(proxy):
    """Release a remote object.

    Parameters:

      proxy (GenericProxy instance):
              Proxy object returned by acquire().
    """
    proxy._ps_conn.eval_in(
        proxy._ps_ns,
        "devices.release(%s)" % (repr(proxy._id),))

def acquireDevice(pythonshareHostspec=None, block=True, acquirer=None,
                  **matchRegexps):
    """Acquire local GUI Test Interface that controls a remote object.

    Parameters:

      pythonshareHostSpec (string, optional):
              [password@]host[:port] of pythonshare-server that hosts
              remotedevices-server. If not given, environment variable
              REMOTEDEVICES_SERVER will be used. If that is undefined,
              "localhost" will be used.

      block (boolean, optional):
              If True, call is blocked until a matching device is acquired.
              Otherwise, the call will return None in case any of the matching
              devices could not be acquired.

      acquirer (string, optional):
              Acquirer id. The default is REMOTEDEVICES_ACQID or an
              empty string.

      property=regexp (optional):
              Requirements for the object. Example:
              d = acquireDevice(display="1280x720", type="android")

    Returns a GUI Test Interface, for instance a fmbtandroid.Device object,
    that will proxy all low-level connection calls to acquired remote object.

    """
    serialNumber, ps_conn, ps_ns = _acquire(pythonshareHostspec, block,
                                            acquirer=acquirer, **matchRegexps)
    if serialNumber:
        info = ps_conn.eval_in(ps_ns, "devices.info(%s)" % (repr(serialNumber),))
    else:
        return None

    if info["type"] in connectionDeviceTypes:
        device = fmbtandroid.Device(connect=False)
        device.setConnection(ConnectionProxy(serialNumber, (ps_conn, ps_ns)))
    else:
        device = GenericProxy(serialNumber, (ps_conn, ps_ns))
    return device

def releaseDevice(device):
    """Release a remote object behind the local device interface.

    Parameters:

      device (GUITestInterface):
              object returned by acquireDevice().
    """
    if isinstance(device, fmbtandroid.Device):
        releaseConnection(device.connection())
        device.setConnection(None)
    elif isinstance(device, GenericProxy):
        release(device)
    else:
        raise ValueError('invalid object "%s"' % (device,))

def acquireConnection(pythonshareHostspec=None, block=True, acquirer=None, **matchRegexps):
    serialNumber, ps_conn, ps_ns = _acquire(pythonshareHostspec, block,
                                            acquirer=acquirer, **matchRegexps)
    if ps_conn == None:
        return None
    return ConnectionProxy(serialNumber, (ps_conn, ps_ns))

def _acquire(pythonshareHostspec=None, block=True, acquirer=None, **matchRegexps):
    if pythonshareHostspec == None:
        pythonshareHostspec = os.getenv("REMOTEDEVICES_SERVER", "localhost")
    ps_ns = "devices"
    try:
        ps_conn = pythonshare.connection(pythonshareHostspec)
    except socket.error, e:
        raise ConnectionError('connecting to remotedevices server "%s" failed (%s)' % (pythonshareHostspec, e))
    if matchRegexps:
        matchCode = ", ".join(["%s=%s" % (r, repr(matchRegexps[r])) for r in matchRegexps])
    else:
        matchCode = ""
    if acquirer == None:
        acquirer = os.getenv("REMOTEDEVICES_ACQID", "")
    serialNumber = ps_conn.eval_in(ps_ns, "devices.acquire(block=%s, acquirer=%s, %s)" % (block, repr(acquirer), matchCode), lock=False)

    if serialNumber == None:
        ps_conn.close()
        return None, None, None
    else:
        return serialNumber, ps_conn, ps_ns

def rescan(pythonshareHostspec=None):
    """Rescan devices on a remotedevices server.

    Parameters:

      pythonshareHostSpec (string, optional):
              [password@]host[:port] of pythonshare-server that hosts
              remotedevices-server. If not given, environment variable
              REMOTEDEVICES_SERVER will be used. If that is undefined,
              "localhost" will be used.
    """
    if pythonshareHostspec == None:
        pythonshareHostspec = os.getenv("REMOTEDEVICES_SERVER", "localhost")
    ps_ns = "devices"
    try:
        ps_conn = pythonshare.connection(pythonshareHostspec)
    except socket.error, e:
        raise ConnectionError('connecting to remotedevices server "%s" failed (%s)' % (pythonshareHostspec, e))
    ps_conn.eval_in(ps_ns, "devices.rescan()")

def releaseConnection(connection):
    ps_conn = connection._ps_conn
    ps_ns = connection._ps_ns
    serialNumber = connection._id
    ps_conn.exec_in(ps_ns, "devices.release(%s)" % (
        repr(serialNumber),), lock=False)

class ConnectionError(Exception):
    pass
