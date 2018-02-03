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

    fmbt_adapterlogtimeformat="%s.%f"
    actionName = "undefined"
    lastExecutedActionName = "undefined"
    testStep = -1
    simulated_actions = []
    adapterlogFilename = "/tmp/fmbt.adapterlog"

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
        end
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
            adapterlogWriter(File.new($_g_adapterlogFilename, "a"),formatAdapterLogMessage(msg))
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
        adapterlogWriter = func
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
        return adapterlogWriter
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

    def adapterlogWriter(fileObj, formattedMsg)
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
        end
        arg_count = len(argspec.args) - kwarg_count
        arglist = []
        for arg in argspec.args[arg_count]
            arglist.push(arg.to_s)
        end
        kwargs = argspec.args[arg_count]
        kwargs.each_with_index do |index, kwarg|
            arglist.push("#{kwarg}='#{argspec.defaults[index]}")
        end
        if argspec.varargs
            arglist.push("*#{argspec.varargs}")
        end
        if argspec.keywords
            arglist.push("**#{argspec.keywords}")
        end
        begin
            funcspec = "#{func.func_name}(#{arglist.join(", ")})"
        rescue
            funcspec = "#{func.func_name}(fmbt.funcSpec error)"
        end
        return funcspec
    end

    module_function
    def fmbt_adapterlogtimeformat; @fmbt_adapterlogtimeformat end
    def fmbt_adapterlogtimeformat= v; @fmbt_adapterlogtimeformat = v end
    def actionName; @actionName end
    def actionName= v; @actionName = v end
    def lastExecutedActionName; @lastExecutedActionName end
    def lastExecutedActionName= v; @lastExecutedActionName = v end
    def testStep; @testStep end
    def testStep= v; @testStep = v end
    def simulated_actions; @simulated_actions end
    def simulated_actions= v; @simulated_actions = v end
    def adapterlogFilename; @adapterlogFilename end
    def adapterlogFilename= v; @adapterlogFilename = v end

end