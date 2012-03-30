import subprocess

fmbt_stats_format = ""
fmbt_stats_output = ""
fmbt_stats_plot = ""
fmbt_stats_logfile = ""
fmbt_stats_redirect = ""

def iExecute():
    stepslogfile = file("teststeps.log","w")
    cmd = "fmbt-stats %s %s %s %s %s" % (
        fmbt_stats_format,
        fmbt_stats_output,
        fmbt_stats_plot,
        fmbt_stats_logfile,
        fmbt_stats_redirect)
    p = subprocess.Popen(cmd, shell=True,
                         stdin  = subprocess.PIPE,
                         stdout = stepslogfile.fileno(),
                         stderr = stepslogfile.fileno())
    p.stdin.close()
    exit_status = p.wait()

    # Check exit status
    if fmbt_stats_logfile.endswith("-0.log"):
        if exit_status != 1:
            raise Exception("exit status != 1 with empy log. Try: " + cmd)
        return None # no further checks for an empty log
    elif exit_status != 0:
        raise Exception("exit status != 0 with non-empty log. Try: " + cmd)

    # Read produced textual statistics
    if fmbt_stats_output.startswith("-o"):
        stats_text = file(fmbt_stats_output[3:]).read()
    elif fmbt_stats_redirect != "":
        stats_text = file("output.txt").read()
    if stats_text.strip() == "":
        raise Exception("empty output file. Try: " + cmd)

def iLogSteps(x):
    global fmbt_stats_logfile
    fmbt_stats_logfile = "stats-input-%s.log" % (x,)

def iFormatTimes(args):
    global fmbt_stats_format
    if args == None:
        fmbt_stats_format = ""
    else:
        fmbt_stats_format = "-f times"
        if args:
            fmbt_stats_format += ":" + args

def iFormatSpeed(args):
    global fmbt_stats_format
    fmbt_stats_format = "-f speed"
    if args:
        fmbt_stats_format += ":" + args

def iFormatDist(args):
    global fmbt_stats_format
    fmbt_stats_format = "-f dist"
    if args:
        fmbt_stats_format += ":" + args

def iOutput(arg):
    global fmbt_stats_output
    global fmbt_stats_redirect
    if arg == 'stdout':
        fmbt_stats_output = ""
        fmbt_stats_redirect = "> output.txt"
    else:
        fmbt_stats_output = "-o output.%s" % (arg,)
        fmbt_stats_redirect = ""

def iPlot(arg):
    global fmbt_stats_plot
    if arg == "":
        fmbt_stats_plot = ""
    else:
        fmbt_stats_plot = "-p plot.%s" % (arg,)
