import subprocess
import glob
import os

fmbt_stats_format = ""
fmbt_stats_output = ""
fmbt_stats_plot = ""
fmbt_stats_logfile = ""
fmbt_stats_redirect = ""

def iExecute():
    for f in glob.glob("stats-output-*"):
        try: os.remove(f)
        except: pass

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
            raise Exception("exit status != 1 with empty log. Try: " + cmd)
        return None # no further checks for an empty log
    elif exit_status != 0:
        raise Exception("exit status != 0 with non-empty log. Try: " + cmd)

    # Read produced statistics text file
    if fmbt_stats_output.startswith("-o"):
        stats_text = file(fmbt_stats_output[3:]).read()
        stats_text_format = fmbt_stats_output.split('.')[-1]
    elif fmbt_stats_redirect != "":
        stats_text = file("stats-output-text.txt").read()
        stats_text_format = "txt"
    if stats_text.strip() == "":
        raise Exception("empty output file. Try: " + cmd)

    # Check that every step seems to be reported
    expected_step_count = int(fmbt_stats_logfile[len("stats-input-"):-len(".log")])
    if fmbt_stats_format.startswith("-f times") or fmbt_stats_format == "":
        # Times stats: sum up numbers in the total column
        if stats_text_format == "txt":
            step_count = sum([int(row[39:49])
                              for row in stats_text.split('\n')[2:]
                              if row])
        elif stats_text_format == "csv":
            step_count = sum([int(row.split(';')[4])
                              for row in stats_text.split('\n')[2:]
                              if row])
        elif stats_text_format == "html":
            step_count = sum([int(row.split('</td><td>')[4])
                             for row in stats_text.split('\n')[3:-2]
                             if row])
        else:
            raise Exception("unknown times output format: %s" % (stats_text_format,))
    elif fmbt_stats_format.startswith("-f speed"):
        # Speed stats: count rows
        if stats_text_format == "txt":
            step_count = stats_text.count('\n')-2
        elif stats_text_format == "csv":
            step_count = stats_text.count('\n')-2
        elif stats_text_format == "html":
            step_count = stats_text.count('\n')-5
        else:
            raise Exception("unknown speed output format: %s" % (stats_text_format,))        
    elif fmbt_stats_format.startswith("-f dist"):
        # Distribution stats: sum up numbers in the matrix. Needs
        # adding one because there's no previous action for the first
        # action, and there's no next action for the last one. This
        # validation is skipped if only unique actions are shown.
        if "uniq" in fmbt_stats_format:
            step_count = expected_step_count # skip the test
        elif stats_text_format == "txt":
            step_count = sum([sum([int(c) for c in row.split('"')[0].split()])
                              for row in stats_text.split('\n')[2:]
                              if row]) + 1
        elif stats_text_format == "csv":
            step_count = sum([sum([int(c) for c in row.split(';')[:-1]])
                              for row in stats_text.split('\n')[2:]
                              if row]) + 1
        elif stats_text_format == "html":
            step_count = sum([sum([int(c) for c in row[8:].split('</td><td>')[:-1]])
                              for row in stats_text.split('\n')[4:]
                              if row]) + 1
        else:
            raise Exception("unknown dist output format: %s" % (stats_text_format,))
    if step_count != expected_step_count:
        raise Exception('text output reports %s steps (expected: %s). Try: %s'
                            % (step_count, expected_step_count, cmd))

    # Check that a non-empty plot file has been created if requested.
    if fmbt_stats_plot.startswith("-p"):
        if "," in fmbt_stats_plot:
            plot_filename = fmbt_stats_plot.split(",")[0][3:]
        else:
            plot_filename = fmbt_stats_plot[3:]
        if not os.stat(plot_filename).st_size > 0:
            raise Exception("zero-length plot file. Try: %s" % (cmd,))

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
        fmbt_stats_redirect = "> stats-output-text.txt"
    else:
        fmbt_stats_output = "-o stats-output-text.%s" % (arg,)
        fmbt_stats_redirect = ""

def iPlot(arg):
    global fmbt_stats_plot
    if arg == "":
        fmbt_stats_plot = ""
    else:
        fmbt_stats_plot = "-p stats-output-plot.%s" % (arg,)
