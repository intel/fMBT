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

import fmbt
import os
import re
import signal
import subprocess
import thread
import time

def _stdouterr(cmd):
    fmbt.adapterlog("<RUN>%s</RUN>" % (' '.join([c.replace('"','\\"') for c in cmd]),))
    env = dict(os.environ)
    env["REMOTEDEVICES_ACQID"] = ""
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        close_fds=True,
        env=env)
    out, err = p.communicate()
    fmbt.adapterlog("<OUT>%s</OUT>" % (out + err,))
    return out + err

def _pipe_reader(fileobj):
    l = True
    while l:
        l = fileobj.readline()
        fmbt.adapterlog("<SERVER>%s</SERVER>" % (l.rstrip()))

_g_server_proc = None
def server_start(cmdline_args=[]):
    global _g_server_proc
    fmbt.adapterlog("server start")
    port=os.getenv("RD_TEST_PORT", "")
    if port:
        port_options = ["-p", port]
    else:
        port_options = []
    _g_server_proc = subprocess.Popen(
        ["remotedevices-server"] + cmdline_args + ["--", "-d"] + port_options,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        close_fds=True)
    thread.start_new_thread(_pipe_reader, (_g_server_proc.stdout,))
    thread.start_new_thread(_pipe_reader, (_g_server_proc.stderr,))
    time.sleep(2)

def ctl(cmdArgs=[], expected=[], not_expected=[]):
    _out = _stdouterr(["remotedevices-ctl"] + cmdArgs)
    _retval = []
    for regexp in expected:
        match = re.search(regexp, _out)
        assert re.search(regexp, _out), '"%s" not in <STDOUTERR>%s</STDOUTERR>' % (regexp, _out)
        _retval.append(match.group(0))

    for regexp in not_expected:
        assert re.search(regexp, _out) == None, '"%s" in <STDOUTERR>%s</STDOUTERR>' % (regexp, _out)
    return _retval

def ctl_acquire(matchArgs=[], expected=[]):
    _out = _stdouterr(["remotedevices-ctl", "acquire"] + matchArgs)
    for regexp in expected:
        assert re.match(regexp, _out), '"%s" does not match "%s"' % (regexp, _out)

def server_terminate():
    fmbt.adapterlog("server terminate")
    try:
        os.kill(_g_server_proc.pid, signal.SIGTERM)
        time.sleep(0.5)
        assert _g_server_proc.poll() == -signal.SIGTERM
    except OSError, e:
        assert "No such process" in str(e)
