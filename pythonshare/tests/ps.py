# ps.aal adapter code

import os
import subprocess
import thread

import fmbt

last_bg_pid = 0

def readlines_to_adapterlog(file_obj, prefix):
    while 1:
        line = file_obj.readline()
        if not line:
            break
        fmbt.adapterlog("%s%s" % (prefix, line))

def soe(cmd, stdin="", cwd=None, env=None):
    """Run cmd, return (status, stdout, stderr)"""
    run_env = dict(os.environ)
    if not env is None:
        run_env.update(env)
    fmbt.adapterlog("%s: soe run %r" % (fmbt.actionName(), cmd))
    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=cwd,
            env=run_env)
        out, err = p.communicate(input=stdin)
    except Exception, e:
        return (None, None, str(e))
    fmbt.fmbtlog("%s: soe got status=%r out=%r err=%r" % (fmbt.actionName(), p.returncode, out, err))
    return (p.returncode, out, err)

def bg(cmd):
    global last_bg_pid
    fmbt.fmbtlog("%s: bg run %r" % (fmbt.actionName(), cmd))
    p = subprocess.Popen(cmd, shell=False,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    fmbt.fmbtlog("%s: bg pid %s" % (fmbt.actionName(), p.pid))
    thread.start_new_thread(readlines_to_adapterlog, (p.stdout, "%s out: " % (p.pid,)))
    thread.start_new_thread(readlines_to_adapterlog, (p.stderr, "%s err: " % (p.pid,)))
    last_bg_pid = p.pid
