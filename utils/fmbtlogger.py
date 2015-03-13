# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
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

"""
fmbtlogger logs method calls, return values and exceptions

Example:

import fmbt
import fmbtlogger
import fmbtandroid

# Log all Device method calls, return values and exceptions to adapter
# log:

d = fmbtlogger.text(fmbtandroid.Device(), fmbt.adapterlog)
d.pressPower()
"""

import datetime
import sys
import traceback
import types

import fmbt

def _formatAction(fmt, actionName):
    values = {
        "action": actionName
        }
    return fmt % values

def _formatKwArgs(kwargs):
    l = []
    for key in sorted(kwargs):
        v = kwargs[key]
        if type(v) == str: l.append("%s=%s" % (key, repr(v)))
        else: l.append("%s=%s" % (key, str(v)))
    return l

def _formatCall(fmt, func, args, kwargs):
    arglist = []
    for a in args:
        if type(a) == str: arglist.append(repr(a))
        else: arglist.append(str(a))
    values = {
        "func": func.__name__,
        "args": ", ".join(arglist),
        "kwargs": ", ".join([""] + _formatKwArgs(kwargs))
        }
    return fmt % values

def _formatRetunValue(fmt, retval):
    if type(retval) == str: values={'value': repr(retval)}
    else: values={'value': str(retval)}
    return fmt % values

def _formatException(fmt):
    s = traceback.format_exc()
    exc, msg, _ = sys.exc_info()
    values = {
        "tb": s,
        "exc": exc.__name__,
        "msg": msg
        }
    return fmt % values

class FileToLogFunc(object):
    def __init__(self, fileObj):
        self._fileObj = fileObj
        if hasattr(self._fileObj, "flush"):
            self._flush = True
        else:
            self._flush = False
    def __call__(self, msg):
        self._fileObj.write("%s\n" % (msg,))
        if self._flush:
            self._fileObj.flush()

class LogWriter(object):
    """
    LogWriter interface has the following methods:

      start(actionName)
              called after the execution of next action in fMBT model
              has started.

      end(actionName)
              called after the execution of previously executed action
              has ended.

      call(func, args, kwargs)
              called before func(args, kwargs) is called in logged
              interface.

      ret(returnValue)
              called after function returned returnValue.

      exc()
              called after function raised exception. The exception
              can be inspected using sys.exc_info().
    """
    defaultFormats = {
        "start": "%(action)s",
        "end": "",
        "call": "%(func)s(%(args)s%(kwargs)s)",
        "ret": "= %(value)s",
        "exc": "! %(exc)s (%(msg)s)"
        }


class CSVLogWriter(LogWriter):
    # TODO: fmbtandroid should add here some checks include screenshots
    # to the log where appropriate
    def __init__(self, logFunc, separator=";", formats=None,
                 callPrefix="", linePrefix=""):
        if formats == None:
            self.formats = CSVLogWriter.defaultFormats
        else:
            self.formats = {}
            for key in CSVLogWriter.defaultFormats:
                self.formats = formats.get(key, CSVLogWriter.defaultFormats[key])
        self.logFunc = logFunc
        self.depth = 0
        self.separator = separator
        self.callPrefix = callPrefix
        self.linePrefix = linePrefix
        if "%" in self.linePrefix:
            self.timeOnLinePrefix = True
        else:
            self.timeOnLinePrefix = False
    def _log(self, msg):
        if len(msg.strip()) > 0:
            columnPrefix = (self.separator * self.depth)
            if self.timeOnLinePrefix:
                linePrefix = fmbt.formatTime(self.linePrefix)
            else:
                linePrefix = self.linePrefix
            self.logFunc(linePrefix + columnPrefix + msg)
    def start(self, actionName):
        msg = _formatAction(self.formats["start"], actionName)
        self._log(msg)
        self.depth += 1
    def end(self, actionName):
        msg = _formatAction(self.formats["end"], actionName)
        self._log(msg)
        self.depth -= 1
    def call(self, func, args, kwargs):
        msg = _formatCall(self.formats["call"], func, args, kwargs)
        self._log(self.callPrefix + msg)
        self.depth += 1
    def ret(self, returnValue):
        self.depth -= 1
        msg = _formatRetunValue(self.formats["ret"], returnValue)
        self._log(msg)
    def exc(self):
        self.depth -= 1
        msg = _formatException(self.formats["exc"])
        self._log(msg)

def csv(obj, logTarget, csvSeparator=";", formats=None, logDepth=1,
        callPrefix="", linePrefix="%s.%f;"):
    """
    Get a proxy object for obj. Methods calls, return values and
    exceptions through the proxy are logged.

    Parameters:

      obj (Python object):
              Object whose function calls will be logged.

      logTarget (function or file-like object):
              Function that gets called with one string argument (log
              message), or a file-like object where log messages will
              be written.

      csvSeparator (string, optional):
              separator between CSV columns. The default is ";".

      logDepth (integer, optional):
              maximum number of nested calls to be logged. The default
              is 1, that is, only the topmost call (from user code) is
              logged. -1 is unlimited.

      callPrefix (string, optional):
              prefix for every logged function call. Handy if several
              objects are logged to the same logTarget. The default is
              "".

      linePrefix (string, optional):
              prefix for every logged line. Prefix can contain
              strftime conversion specifications. The default is
              "%s.%f ", that is number of seconds since the Epoch
              followed by "." and microseconds.

    Returns a proxy object for obj.
    """

    if type(logTarget) == types.FunctionType:
        logWriter = CSVLogWriter(logTarget, separator=csvSeparator,
                                 callPrefix=callPrefix, linePrefix=linePrefix)
    elif hasattr(logTarget, "write"):
        logWriter = CSVLogWriter(FileToLogFunc(logTarget),
                                 separator=csvSeparator, formats=formats,
                                 callPrefix=callPrefix, linePrefix=linePrefix)
    else:
        raise TypeError("logTarget must be a function or a writable file(-like) object")
    return raw(obj, logWriter, logDepth)

def text(obj, logTarget, indentDepth=4, formats=None, logDepth=1,
         callPrefix="", linePrefix="%s.%f "):
    """
    Get a proxy object for obj. Methods calls, return values and
    exceptions through the proxy are logged.

    Parameters:

      obj (Python object):
              Object whose function calls will be logged.

      logTarget (function or file-like object):
              Function that gets called with one string argument (log
              message), or a file-like object where log messages will
              be written.

      indentDepth (integer, optional):
              number of spaces when indenting nested log calls.  The
              default is 4.

      logDepth (integer, optional):
              maximum number of nested calls to be logged. The default
              is 1, that is, only the topmost call (from user code) is
              logged. -1 is unlimited.

      callPrefix (string, optional):
              prefix for every logged function call. Handy if several
              objects are logged to the same logTarget. The default is
              "".

      linePrefix (string, optional):
              prefix for every logged line. Prefix can contain
              strftime conversion specifications. The default is
              "%s.%f ", that is number of seconds since the Epoch
              followed by "." and microseconds.

    Returns a proxy object for obj.
    """
    return csv(obj, logTarget, csvSeparator = " "*indentDepth, formats=formats,
               logDepth=logDepth, callPrefix=callPrefix, linePrefix=linePrefix)

def raw(obj, logWriter, logDepth=1):
    if not isinstance(logWriter, LogWriter):
        raise TypeError("LogWriter instance expected as the second parameter")
    if type(obj) in [types.TypeType, types.ClassType]:
        return _logInstances(obj, logWriter, logDepth)
    else:
        return _logCalls(obj, logWriter, logDepth)

def _logInstances(orig_class, report, logDepth):
    def _detectInstantiations(*args, **kwargs):
        orig_self = orig_class(*args, **kwargs)
        return _logCalls(orig_self, report, logDepth)
    return _detectInstantiations

def _logCalls(orig_self, report, logDepth_):
    """
    logger(object) starts logging method calls of the object
    """
    class localVars: pass
    localVars.logDepth = logDepth_
    localVars.testStep = -1
    localVars.actionName = None
    def logMethodCall(func, throughInstance = None):
        def fmbtlogger_wrap(*args, **kwargs):
            currentTestStep = fmbt.getTestStep()
            if localVars.testStep != currentTestStep:
                if localVars.actionName not in [None, "undefined"]:
                    report.end(localVars.actionName)
                localVars.testStep = currentTestStep
                localVars.actionName = fmbt.getActionName()
                if localVars.actionName not in [None, "undefined"]:
                    report.start(localVars.actionName)
            if localVars.logDepth == 0:
                return func(*args, **kwargs)
            report.call(func, args, kwargs)
            localVars.logDepth -= 1
            try:
                if throughInstance:
                    rv = func.im_func(throughInstance, *args, **kwargs)
                else:
                    rv = func(*args, **kwargs)
                report.ret(rv)
            except:
                report.exc()
                localVars.logDepth += 1
                raise
            localVars.logDepth += 1
            return rv
        fmbtlogger_wrap.__doc__ = "%s\n%s" % (
            fmbt.funcSpec(func), func.__doc__)
        return fmbtlogger_wrap
    class _detectCalls(orig_self.__class__):
        __doc__ = orig_self.__class__.__doc__
        def __init__(self): pass
        def __del__(self): pass
        def __getattribute__(self, attr):
            attr = getattr(orig_self, attr)
            if type(attr) == types.MethodType:
                if localVars.logDepth == 0:
                    rv = logMethodCall(attr)
                else:
                    rv = logMethodCall(attr, throughInstance = self)
                return rv
            else:
                return attr
        def __setattr__(self, attr, value):
            setattr(orig_self, attr, value)
    return _detectCalls()
