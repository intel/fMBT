# fMBT, free Model Based Testing tool
# Copyright (c) 2012-2017 Intel Corporation.
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

# Import this to test step implementations written in Python
# in order to enable logging.

# fmbtlog writes given message to the fmbt log (XML)
#         messages can be viewed using format $al of
#         fmbt-log -f '$al' logfile
#
# adapterlog writes given message to the adapter log (plain text)
#         written by remote_python or remote_pyaal, for instance.

# Log function implementations are provided by the adapter
# component such as remote_python or remote_pyaal.

module Fmbt 

    $_g_fmbt_adapterlogtimeformat="%s.%f"
    $_g_actionName = "undefined"
    $_g_lastExecutedActionName = "undefined"
    $_g_testStep = -1
    $_g_simulated_actions = []
    $_g_adapterlogFilename = "/tmp/fmbt.adapterlog"


    def _fmbt_call_helper(func,param = "")
        if simulated()
            return ""
        end
        $stdout.write("fmbt_call #{func}.#{param}\n")
        sys.stdout.flush()
        response = sys.stdin.readline().rstrip()
        magic,code = response.split(" ")
        if magic == "fmbt_call"
            if code[0] == "1"
                return urllib.unquote(code[1])
            end
        end
        return ""
    end

    def formatTime(timeformat="%s", timestamp=None)
        if timestamp == None
            timestamp = datetime.datetime.now()
        # strftime on Windows does not support conversion to epoch (%s).
        # Calculate it here, if needed.
        if os.name == "nt"
            if timeformat.include?("%s")
                epoch_time = time.mktime(timestamp.timetuple())
                timeformat = timeformat.replace("%s", str(int(epoch_time)))
            end
            if timeformat.include?("%F")
                timeformat = timeformat.replace("%F", "%Y-%m-%d")
            end
            if timeformat.include?("%T")
                timeformat = timeformat.replace("%T", "%H%M%S")
            end
        end
        return timestamp.strftime(timeformat)
    end

    def heuristic()
        return _fmbt_call_helper("heuristic.get")
    end

    def setHeuristic(heuristic)
        return _fmbt_call_helper("heuristic.set",heuristic)
    end

    def coverage()
        return _fmbt_call_helper("coverage.get")
    end

    def setCoverage(coverage)
        return _fmbt_call_helper("coverage.set",coverage)
    end

    def coverageValue()
        return _fmbt_call_helper("coverage.getValue")
    end

    def fmbtlog(msg, flush=True)
        begin 
            File.new("/tmp/fmbt.fmbtlog", "a").write("#{msg} \n")
        rescue 
        end
    end

    def fmbtlograw(msg, flush=True)
        begin 
            File.new("/tmp/fmbt.fmbtlog", "a").write("#{msg} \n")
        rescue 
        end
    end

    def adapterlog(msg, flush=True)
        begin
            $_adapterlogWriter(File.new($_g_adapterlogFilename, "a"),formatAdapterLogMessage(msg))
        rescue 
        end
    end

    def setAdapterLogWriter(func)
        """
        Override low-level adapter log writer with the given function. The
        function should take two parameters a file-like object and a log
        message. The message is formatted and ready to be written to the
        file. The default is

        lambda fileObj, formattedMsg fileObj.write(formattedMsg)
        """
        $_adapterlogWriter = func
    end

    def adapterLogFilename()
        """
        Returns the filename to which the default fmbt.adapterlog() is
        writing.
        """
        return $_g_adapterlogFilename
    end

    def setAdapterLogFilename(filename)
        """
        Set filename to which the default fmbt.adapterlog() function will
        write messages
        """
        global $_g_adapterlogFilename
        $_g_adapterlogFilename = filename
    end

    def adapterLogWriter()
        """
        Return current low-level adapter log writer function.
        """
        return $_adapterlogWriter
    end

    def reportOutput(msg)
        begin 
            File.new("/tmp/fmbt.reportOutput", "a").write("#{msg} \n")
        rescue 
        end
    end

    def setAdapterLogTimeFormat(strftime_format)
        """
        Use given time format string in timestamping adapterlog messages
        """
        global $_g_fmbt_adapterlogtimeformat
        $_g_fmbt_adapterlogtimeformat = strftime_format
    end

    def formatAdapterLogMessage(msg, fmt="%s %s\n")
        """
        Return timestamped adapter log message as a string (not unicode)
        """
        s = fmt % [formatTime($_g_fmbt_adapterlogtimeformat), msg]
        if type(s) == unicode
            s = s.encode("utf8")
        end
        return s
    end

    def getActionName()
        """deprecated, use actionName()"""
        return $_g_actionName
    end

    def actionName()
        """
        Return the name of currently executed action (input or output).
        """
        return $_g_actionName
    end

    def lastExecutedActionName()
        """
        Return the name of the previously executed action.

        Counts only really executed actions, not simulated.
        """
        return $_g_lastExecutedActionName
    end

    def getTestStep()
        """deprecated, use testStep()"""
        return $_g_testStep
    end

    def testStep()
        """
        Return the number of currently executed test step.
        """
        return $_g_testStep
    end

    def simulated()
        """
        Returns True if fMBT is simulating execution of an action (guard
        or body block) instead of really executing it.
        """
        return len($_g_simulated_actions) > 0
    end

    def $_adapterlogWriter(fileObj, formattedMsg)
        fileObj.write(formattedMsg)
    end

    def funcSpec(func)
        """
        Return function name and args as they could have been defined
        based on function object.
        """
        argspec = inspect.getargspec(func)
        if argspec.defaults
            kwarg_count = len(argspec.defaults)
        else
            kwarg_count = 0
        arg_count = len(argspec.args) - kwarg_count
        arglist = [str(arg) for arg in argspec.args[arg_count]]
        kwargs = argspec.args[arg_count]
        for index, kwarg in enumerate(kwargs)
            arglist.append("%s=%s" % (kwarg, repr(argspec.defaults[index])))
        if argspec.varargs
            arglist.append("*%s" % (argspec.varargs,))
        if argspec.keywords
            arglist.append("**%s" % (argspec.keywords,))
        begin
            funcspec = "%s(%s)" % (func.func_name, ", ".join(arglist))
        rescue
            funcspec = "%s(fmbt.funcSpec error)" % (func.func_name,)
        end
        return funcspec
    end

    $_g_debug_socket = None
    $_g_debug_conn = None

    def debug(session=0)
        """
        Start debugging with fmbt-debug from the point where this function
        was called. Execution will stop until connection to fmbt-debug
        [session] has been established.

        Parameters

        session (integer, optional)
                debug session that identifies which fmbt-debug should
                connect to this process. The default is 0.

        Example

        - execute on command line "fmbt-debug 42"
        - add fmbt.debug(42) in your Python code
        - run the Python code so that it will call fmbt.debug(42)
        - when done the debugging on the fmbt-debug prompt, enter "c"
            for continue.
        """
        import bdb
        import inspect
        import pdb
        import socket

        if not $_g_debug_socket
            PORTBASE = 0xf4bd # 62653, fMBD
            host = "127.0.0.1" # accept local host only, by default
            port = PORTBASE + session
            $_g_debug_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            begin
                $_g_debug_socket.bind((host, port))
                $_g_debug_socket.listen(1)
                while True
                    ($_g_debug_conn, addr) = $_g_debug_socket.accept()
                    $_g_debug_conn.sendall("fmbt.debug\n")
                    msg = $_g_debug_conn.recv(len("fmbt-debug\n"))
                    if msg.startswith("fmbt-debug")
                        break
                    end
                    $_g_debug_conn.close()
                end
            rescue socket.error
                # already in use, perhaps fmbt-debug is already listening to
                # the socket and waiting for this process to connect
                begin
                    $_g_debug_socket.connect((host, port))
                    $_g_debug_conn = $_g_debug_socket
                    whos_there = $_g_debug_conn.recv(len("fmbt-debug\n"))
                    if not whos_there.startswith("fmbt-debug")
                        $_g_debug_conn.close()
                        $_g_debug_socket = None
                        $_g_debug_conn = None
                        raise ValueError(
                            'unexpected answer "%s", fmbt-debug expected' %
                            (whos_there.strip(),))
                    end
                    $_g_debug_conn.sendall("fmbt.debug\n")
                rescue socket.error
                    raise ValueError('debugger cannot listen or connect to %s%s' % (host, port))
                end
        end
        end
        if not $_g_debug_conn
            fmbtlog("debugger waiting for connection at %s%s" % (host, port))
        end
        # socket.makefile does not work due to buffering issues
        # therefore, use our own socket-to-file converter
        class SocketToFile(object)
            def __init__(self, socket_conn)
                self._conn = socket_conn
            end
            def read(self, bytes=-1)
                msg = []
                rv = ""
                begin
                    c = self._conn.recv(1)
                rescue KeyboardInterrupt
                    self._conn.close()
                    raise
                end
                while c and not rv
                    msg.append(c)
                    if c == "\r"
                        rv = "".join(msg)
                    elsif c == "\n"
                        rv = "".join(msg)
                    elsif len(msg) == bytes
                        rv = "".join(msg)
                    else
                        c = self._conn.recv(1)
                    end
                end
                return rv
            end
            def readline(self)
                return self.read()
            end
            def write(self, msg)
                self._conn.sendall(msg)
            end
            def flush(self)
                pass
            end
        end
        connfile = SocketToFile($_g_debug_conn)
        debugger = pdb.Pdb(stdin=connfile, stdout=connfile)
        debugger.set_trace(inspect.currentframe().f_back)
    end

end