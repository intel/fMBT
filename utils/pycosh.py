#!/usr/bin/env python2
# fMBT, free Model Based Testing tool
# Copyright (c) 2016, Intel Corporation.
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

# This library implements pico-sized multiplatform shell

"""Pico-sized multiplatform shell
"""

# pylint: disable = redefined-builtin, eval-used, exec-used, invalid-name
# pylint: disable = missing-docstring, global-statement, unneeded-not
# pylint: disable = bare-except, broad-except, too-many-branches
# pylint: disable = singleton-comparison

import atexit
import base64
import datetime
import difflib
import fnmatch
import getopt
import getpass
import glob
import inspect
import md5
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import types
import urllib2
import zipfile

try:
    import pythonshare
except ImportError:
    pythonshare = None

if os.name == "nt":
    import ctypes

_g_pipe_filename = "pycosh.pipe.%s" % (os.getpid(),)
_g_pipe_has_data = False
_g_pyenv = {}

def _file(filename, mode="rb"):
    try:
        return file(filename, mode)
    except IOError, e:
        raise ValueError(str(e).replace(":", ""))

def _write_b64(filename, b64data):
    file(filename, "wb").write(base64.b64decode(b64data))

def _getopts(args, shortopts, longopts=()):
    try:
        opts, remainder = getopt.gnu_getopt(args, shortopts, longopts)
    except getopt.GetoptError, e:
        raise Exception("Options: -%s (%s)" % (shortopts, e))
    return dict(opts), remainder

def _human_readable_size(size):
    scale = "BkMGTPEZY"
    divisions = 0
    while size >= 1000:
        size = size / 1024.0
        divisions += 1
    return "%.1f%s" % (size, scale[divisions])

def _output(s):
    sys.stdout.write(s)
    sys.stdout.write("\n")
    sys.stdout.flush()

def _shell_soe(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        status = p.returncode
    except OSError:
        status, out, err = None, None, None
    if out != None and sys.stdout.encoding:
        out = out.decode(sys.stdout.encoding).encode("utf-8")
    if err != None and sys.stderr.encoding:
        err = err.decode(sys.stderr.encoding).encode("utf-8")
    return status, out, err

def cmd2py(cmdline):
    if "|" in cmdline:
        cmd_left, cmd_right = cmdline.split("|", 1)
        funccall = "pipe(%s, %s)" % (repr(cmd2py(cmd_left)),
                                     repr(cmd2py(cmd_right)))
    elif ">" in cmdline:
        cmd_left, filename = cmdline.split(">", 1)
        funccall = "pipe(%s, %s)" % (
            repr(cmd2py(cmd_left)),
            repr("redir('%s')" % (filename.strip(),)))
    else:
        cmdline_list = shlex.split(cmdline.strip())
        funcname = cmdline_list[0]
        args = cmdline_list[1:]
        funccall = funcname + repr(tuple(args))
    return funccall

def prompt():
    """prompt
    print prompt"""
    try:
        user = getpass.getuser()
    except Exception:
        user = ""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = ""
    return (user + "@" +
            hostname + ":" +
            os.getcwd() + ": ")

def awk(prog, *args):
    """awk PROG [FILE...]
    PROG syntax: [/REGEXP/]{print $N...}"""
    filenames = expand(*args, accept_pipe=True).splitlines()
    if not filenames:
        raise ValueError("missing input")
    rv = []
    awk_syntax = re.compile('(/([^/]*)/)?\{([^}]*)\}')
    parsed_prog = awk_syntax.match(prog)
    if not parsed_prog:
        raise ValueError('syntax error in awk program')
    awk_pattern = parsed_prog.group(2)
    if not awk_pattern is None:
        awk_pattern_re = re.compile(awk_pattern)
    else:
        awk_pattern_re = re.compile("")
    awk_statements = [s.strip() for s in parsed_prog.group(3).split(";")]
    awk_fieldno_re = re.compile("\$([0-9]+)")
    awk_fieldsep_re = re.compile("[ \n\t\r]*")
    for filename in filenames:
        for line in open(filename).xreadlines():
            if awk_pattern_re.search(line):
                for stmt in awk_statements:
                    if stmt.startswith("print"):
                        what = stmt[5:].strip()
                        if not what:
                            # plain "print" results in full line
                            what = "$0"
                        else:
                            # no variable handling for now...
                            what = what.replace('"', '')
                        fields = [int(n) for n in awk_fieldno_re.findall(what)]
                        translate = {}
                        if fields:
                            line_fields = [line.splitlines()[0]] + [
                                l for l in awk_fieldsep_re.split(line) if l]
                            for field in fields:
                                if field < len(line_fields):
                                    translate["$" + str(field)] = line_fields[field]
                                else:
                                    translate["$" + str(field)] = ""
                            for rep in reversed(sorted(translate.keys())):
                                # if not reversed, might replace $1 before $10
                                what = what.replace(rep, translate[rep])
                        rv.append(what)
    return "\n".join(rv)

def cd(dirname):
    """cd DIRNAME
    change current working directory"""
    d = expand(dirname, accept_pipe=False, min=1, exist=True).splitlines()
    if len(d) > 1:
        raise ValueError("unambiguous directory name")
    os.chdir(os.path.join(os.getcwd(), d[0]))
    return ""

def curl(*args):
    """curl [-x P][-o FILE] URL
    download URL (use proxy P), save to FILE"""
    opts, urls = _getopts(args, "x:o:")
    rv = []
    if not urls:
        raise ValueError("missing URL(s)")
    if "-x" not in opts and "http_proxy" in _g_pyenv:
        opts["-x"] = _g_pyenv.get("http_proxy")
    if "-x" in opts:
        proxy = urllib2.ProxyHandler({
            'http': opts["-x"],
            'https': opts["-x"],
            'ftp': opts["-x"]})
    else:
        proxy = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
    for url in urls:
        data = urllib2.urlopen(url).read()
        if "-o" in opts:
            _file(opts["-o"], "a").write(data)
        else:
            rv.append(data)
    return "".join(rv)

def find(*args):
    """find [-n FILE] DIR
    find file(s) in directory"""
    opts, remainder = _getopts(args, "n:")
    if not remainder:
        raise ValueError("missing DIR")
    dirname = remainder[0]
    if "-n" in opts:
        findname = opts["-n"]
    else:
        findname = "*"
    dirname_ends_with_sep = dirname[-1] in ["/", "\\"]
    slash_only = not "\\" in dirname
    if slash_only:
        sep = "/"
    else:
        sep = os.path.sep
    rv = []
    # DIR + NAME forms a path without duplicate path separators
    for root, dirs, files in os.walk(dirname):
        if slash_only:
            root = root.replace("\\", "/")
        for name in dirs + files:
            if fnmatch.fnmatch(name, findname):
                if root == dirname:
                    if dirname_ends_with_sep:
                        rv.append(name)
                    else:
                        rv.append(sep + name)
                else:
                    rv.append(root[len(dirname):] + sep + name)
    return "\n".join(rv)

def date():
    """date
    print current date and time"""
    t = datetime.datetime.now()
    return t.strftime("%Y-%m-%d %H:%M:%S.") + str(t.microsecond)

def diff(*args):
    """diff FILE1 FILE2
    print differences between two files"""
    files = expand(*args).splitlines()
    try:
        file1, file2 = files
    except Exception:
        raise ValueError("exactly two files required")
    lines1 = _file(file1).readlines()
    lines2 = _file(file2).readlines()
    udiff = difflib.unified_diff(lines1, lines2, file1, file2)
    # append endlines to lines where it is missing
    difflines = [l + ["", "\n"][l[-1] != "\n"] for l in udiff]
    return "".join(difflines)

def du(*args):
    """du [-h] FILE...
    print [human readable] disk usage of FILEs"""
    opts, filenames = _getopts(args, "h")
    if "-h" in opts:
        size_formatter = _human_readable_size
    else:
        size_formatter = lambda size: str(size)
    filenames = expand(*filenames, accept_pipe=False, min=1).splitlines()
    total_size = 0
    retval = []
    for direntry in filenames:
        size = None
        if os.path.isdir(direntry):
            for root, dirs, filelist in os.walk(direntry):
               for filename in filelist:
                   fullname = os.path.join(root, filename)
                   size = os.stat(fullname).st_size
                   retval.append("%-8s %s" % (size_formatter(size), fullname))
                   total_size += size
        elif os.path.isfile(direntry):
            size = os.stat(direntry).st_size
            total_size += size
            retval.append("%-8s %s" % (size_formatter(size), direntry))
    retval.append(size_formatter(total_size))
    return "\n".join(retval)

def echo(*args):
    return " ".join(args)

def env():
    """env
    print environment variables"""
    rv = []
    for key in sorted(_g_pyenv.keys()):
        rv.append("%s=%s" % (key, repr(_g_pyenv[key])))
    return "\n".join(rv)

def expand(*filenames, **kwargs):
    accept_pipe = kwargs.get("accept_pipe", True)
    min_count = kwargs.get("min", 0)
    must_exist = kwargs.get("exist", False)
    rv = []
    if not filenames:
        if accept_pipe and _g_pipe_has_data:
            rv.append(_g_pipe_filename)
    else:
        for pattern in filenames:
            extends_to = glob.glob(pattern)
            if extends_to:
                for filepath in extends_to:
                    if "/" in filepath and "\\" in filepath:
                        filepath = filepath.replace('\\', '/')
                    rv.append(filepath)
            elif not must_exist:
                rv.append(pattern)
    if not min_count <= len(rv):
        raise ValueError("expected at least %s file(s), got %s" %
                         (min_count, len(rv)))
    return "\n".join(rv)

def export(assignment):
    """export VAR=VALUE
    assign VALUE to environment variable VAR"""
    if not "=" in assignment or not assignment.split("=")[0].strip():
        raise ValueError("expected VAR=VALUE")
    _g_pyenv.__setitem__(*assignment.split("=", 1))
    return ""

def grep(pattern, *filenames):
    """grep PATTERN [FILE...]
    show matching lines in file(s)"""
    matching_lines = []
    all_files = expand(*filenames).splitlines()
    for filename in all_files:
        for line in file(filename).xreadlines():
            if pattern in line:
                matching_lines.append(line)
    return "".join(matching_lines)

def head(*args):
    """head [-n NUM] [FILE...]
    show first NUM lines in file(s)"""
    opts, filenames = _getopts(args, "n:")
    all_files = expand(*filenames).splitlines()
    if "-n" in opts:
        lines = int(opts["-n"])
    else:
        lines = 10
    rv = []
    for filename in all_files:
        line_count = 0
        for line in file(filename).xreadlines():
            line_count += 1
            if line_count > lines:
                break
            rv.append(line)
    return "".join(rv)

def help(func=None):
    """help [COMMAND]
    print help (on COMMAND)"""
    if not func:
        rv = []
        for c in globals().keys():
            if c.startswith("_"):
                continue
            if not isinstance(globals()[c], types.FunctionType):
                continue
            if not globals()[c].__doc__:
                continue
            if len(globals()[c].__doc__.splitlines()) != 2:
                continue
            rv.append("%-26s%s" %
                      tuple([l.strip() for l in
                             globals()[c].__doc__.splitlines()]))
        rv = sorted(rv)
    elif isinstance(globals().get(func, None), types.FunctionType):
        rv = inspect.getsource(globals().get(func)).splitlines()
    return "\n".join(rv)

def kill(*pids):
    """kill PID...
    terminate processes"""
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)
    return ""

def ls(*args):
    """ls [-l]
    list files on current working directory"""
    opts, filenames = _getopts(args, "l")
    if filenames:
        files = sorted([f for f in expand(*filenames, exist=True).splitlines()])
    else:
        _, subdirs, files = os.walk(".").next()
        files = sorted([d + "/" for d in subdirs]) + sorted(files)
    if "-l" in opts:
        rv = []
        for f in files:
            fstat = os.stat(f)
            rv.append("%10s  %s  %s" % (
                fstat.st_size,
                time.strftime("%Y-%m-%d %H:%M", time.localtime(fstat.st_mtime)),
                f))
    else:
        rv = files
    return "\n".join(rv)

def nl(*filenames):
    """nl FILE...
    number lines"""
    all_files = expand(*filenames).splitlines()
    rv = []
    line_no = 0
    for filename in all_files:
        for line in file(filename).xreadlines():
            line_no += 1
            rv.append("%5s  %s" % (line_no, line))
    return "".join(rv)

def mkdir(*args):
    """mkdir [-p] DIRNAME...
    make directories, -p: intermediates if necessary"""
    args, dirnames = _getopts(args, "-p")
    for dirname in dirnames:
        if "-p" in args:
            os.makedirs(dirname)
        else:
            os.mkdir(dirname)
    return ""

def redir(dst_filename):
    # redirect data from input pipe to a file
    src_filename = expand(accept_pipe=True)
    if src_filename:
        file(dst_filename, "wb").write(
            file(src_filename, "rb").read())
    return ""

def rm(*args):
    """rm [-r] FILE...
    remove file"""
    args, filenames = _getopts(args, "-r")
    filenames = expand(*filenames, accept_pipe=False, min=1).splitlines()
    for filename in filenames:
        if "-r" in args and os.path.isdir(filename):
            shutil.rmtree(filename)
        else:
            os.remove(filename)
    return ""

def rmdir(dirname):
    """rmdir DIRNAME
    remove directory"""
    os.rmdir(dirname)
    return ""

def cat(*filenames):
    """cat FILE...
    concatenate contents of listed files"""
    return "".join([file(f).read() for f in expand(*filenames).splitlines()])

def df(*args):
    """df [-h] DIRNAME
    print [human readable] free space on DIRNAME"""
    args, dirnames = _getopts(args, "-h")
    if "-h" in args:
        human_readable = True
    else:
        human_readable = False
    try:
        dirname = dirnames[0]
    except IndexError:
        raise Exception("directory name missing")
    if os.name == "nt": # Windows
        cfree = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(dirname), None, None,
            ctypes.byref(cfree))
        free = cfree.value
    else:  # Posix
        st = os.statvfs(dirname)
        free = st.f_bavail * st.f_frsize
    if human_readable:
        retval = _human_readable_size(free)
    else:
        retval = str(free)
    return retval

def md5sum(*filenames):
    """md5sum FILE...
    print MD5 (128-bit) checksums."""
    rv = []
    for filename in expand(*filenames).splitlines():
        rv.append("%-34s%s" %
                  (md5.md5(file(filename, "rb").read()).hexdigest(),
                   filename))
    return "\n".join(rv)

def mv(src, dst):
    """mv SOURCE DEST
    move file or directory to destination"""
    shutil.move(src, dst)
    return ""

def cp(src, dst):
    """cp SOURCE DEST
    copy file or directory to destination"""
    shutil.copy(src, dst)
    return ""

def pipe(expr_left, expr_right):
    global _g_pipe_has_data
    try:
        pipe_in_data = eval(expr_left)
        file(_g_pipe_filename, "wb").write(pipe_in_data)
        del pipe_in_data
        _g_pipe_has_data = True
        rv = eval(expr_right)
    finally:
        try:
            os.remove(_g_pipe_filename)
        except Exception:
            pass
        _g_pipe_has_data = False
    return rv

def ps(*args):
    """ps [-v] [PID...]
    list processes (-v virtual memory)"""
    args, pids = _getopts(args, "-v")
    rv = []
    pids = set(pids)
    if os.name == "nt":
        if "-v" in args:
            opt_field = "PageFileUsage"
        else:
            opt_field = "parentprocessid"
        _, o, _ = _shell_soe(
            "wmic process get %s,processid,description,commandline" %
            (opt_field,))
        for line in o.splitlines():
            try:
                cmd_desc_almostlast, lastfield = line.rstrip().rsplit(" ", 1)
                cmd_desc, almostlast = (
                    cmd_desc_almostlast.rstrip().rsplit(" ", 1))
                cmd, desc = cmd_desc.rstrip().rsplit(" ", 1)
                if opt_field == "PageFileUsage":
                    pid = lastfield
                    pdata = almostlast # PageFileUsage
                else:
                    pid = lastfield
                    pdata = almostlast # parent pid
                if not desc.lower() in cmd.strip().lower():
                    cmd = "[%s] %s" % (desc.strip(), cmd.strip())
                if not pids or pid in pids:
                    rv.append("%8s %8s %s" %
                              (pid.strip(), pdata.strip(), cmd.strip()))
            except Exception:
                pass
    else:
        if "-v" in args:
            opt_field = "size"
        else:
            opt_field = "ppid"
        _, o, _ = _shell_soe("ps ax -o%s,pid,cmd" % (opt_field,))
        for line in o.splitlines():
            pdata, pid, cmd = line.strip().split(None, 2)
            if not pids or pid in pids:
                rv.append("%8s %8s %s" % (pid, pdata, cmd.strip()))
    return "\n".join(rv)

def psh(*cmd):
    """psh COMMAND
    run COMMAND in powershell (Windows)"""
    _, o, e = _shell_soe(
        ("powershell.exe",) + cmd)
    return o + e

_g_pspycosh_conn = None
def pspycosh(psconn):
    """pspycosh HOSTSPEC
    open pycosh shell on a pythonshare server"""
    global _g_pspycosh_conn
    if isinstance(psconn, pythonshare.client.Connection):
        _g_pspycosh_conn = psconn
    else:
        _g_pspycosh_conn = pythonshare.connect(psconn)
    _g_pspycosh_conn.exec_(_g_pycosh_source)
    return ""

def psput(psconn, pattern):
    """psput CONNSPEC FILE...
    upload files to pythonshare server"""
    if isinstance(psconn, pythonshare.client.Connection):
        conn = psconn
        close_connection = False
    else:
        conn = pythonshare.connect(psconn)
        close_connection = True
    conn.exec_("import base64")
    rv = []
    for filename in expand(pattern, accept_pipe=False).splitlines():
        data = file(filename).read()
        conn.eval_('file(%s, "wb").write(base64.b64decode(%s))' %
                   (repr(os.path.basename(filename)),
                    repr(base64.b64encode(data))))
        rv.append(filename)
    if close_connection:
        conn.close()
    return "\n".join(rv)

def psget(psconn, pattern):
    """psget CONNSPEC FILE...
    download files from pythonshare server"""
    if isinstance(psconn, pythonshare.client.Connection):
        conn = psconn
        close_connection = False
    else:
        conn = pythonshare.connect(psconn)
        close_connection = True
    conn.exec_("".join(inspect.getsourcelines(expand)[0]))
    conn.exec_("import glob")
    rv = []
    for filename in conn.eval_('expand(%s, accept_pipe=False)' %
                               repr(pattern)).splitlines():
        file(os.path.basename(filename), "w").write(
            conn.eval_("file(%s, 'rb').read()" % (repr(filename),)))
        rv.append(filename)
    return "\n".join(rv)

def pwd():
    """pwd
    print current working directory"""
    return os.getcwd()

def pye(*code):
    """pye CODE
    evaluate Python CODE"""
    code = " ".join(code)
    if _g_pipe_has_data:
        _g_pyenv["pipe_in"] = file(expand(accept_pipe=True), "rb")
    try:
        return str(eval(code, globals(), _g_pyenv))
    finally:
        if "pipe_in" in _g_pyenv:
            del _g_pyenv["pipe_in"]

def pyx(*code):
    """pyx CODE
    execute Python CODE"""
    code = " ".join(code)
    if _g_pipe_has_data:
        _g_pyenv["pipe_in"] = file(expand(accept_pipe=True), "rb")
    try:
        try:
            exec code in globals(), _g_pyenv
        except Exception, e:
            return str(e)
    finally:
        if "pipe_in" in _g_pyenv:
            del _g_pyenv["pipe_in"]
    return ""

def sed(cmd, *filenames):
    """sed s/P/R[/N] [FILE]
    replace P with R in FILE"""
    rv = []
    try:
        pattern, repl, count = re.findall("s/([^/]*)/([^/]*)/(.*)", cmd)[0]
        pattern = re.compile(pattern)
    except:
        raise ValueError('invalid command "%s"' % (cmd,))
    all_files = expand(*filenames).splitlines()
    for filename in all_files:
        for line in file(filename).readlines():
            try:
                count_arg = (int(count),)
            except:
                if count == "g":
                    count_arg = ()
                elif count == "":
                    count_arg = (1,)
                else:
                    raise ValueError('invalid count: "%s"' % (count,))
            rv.append(re.subn(* ((pattern, repl, line) + count_arg))[0])
    return "".join(rv)

def sh(*cmd):
    """sh COMMAND
    run COMMAND in shell"""
    s, o, e = _shell_soe(" ".join(cmd))
    return "[exit status: %s]\n%s" % (s, o+e)

def sleep(seconds):
    """sleep SECONDS
    sleep for SECONDS (float)"""
    time.sleep(float(seconds))
    return ""

def sort(*args):
    """sort [-n] [-k N] [FILE]
    sort lines [numerically] according to column N"""
    opts, filenames = _getopts(args, "k:n")
    filenames = expand(*filenames, accept_pipe=True).splitlines()
    rv = []
    for filename in filenames:
        lines = [[l.split(), l] for l in file(filename).readlines()]
        if "-k" in opts:
            k = int(opts["-k"]) - 1
            for line in lines:
                line[0][0], line[0][k] = line[0][k], line[0][0]
        if "-n" in opts:
            for line in lines:
                try:
                    line[0][0] = int(line[0][0])
                except:
                    pass
        lines.sort()
        rv.extend([line[1] for line in lines])
    return "".join(rv)

def sync():
    """sync
    flush system write back caches"""
    if os.name == "nt":
        retval = str(ctypes.windll.kernel32.SetSystemFileCacheSize(-1, -1, 0))
    else:
        _, _, retval = _shell_soe("sync")
    return retval

def tail(*args):
    """tail [-n NUM] [FILE...]
    show last NUM lines in file(s)"""
    opts, filenames = _getopts(args, "n:")
    all_files = expand(*filenames).splitlines()
    if "-n" in opts:
        lines = int(opts["-n"])
    else:
        lines = 10
    rv = []
    if lines > 0:
        for filename in all_files:
            rv.extend(file(filename).readlines()[-lines:])
    return "".join(rv)

def tar(*args):
    """tar [-ctxf] PKG [FILE...]
    create/list/extract a tar package"""
    opts, filenames = _getopts(args, "ctxf:")
    pkg = opts.get("-f", expand(accept_pipe=True))
    if not pkg:
        raise ValueError("package filename missing (-f)")
    rv = []
    if "-t" in opts:
        tf = tarfile.TarFile.open(pkg)
        rv.extend(tf.getnames())
    elif "-x" in opts:
        tf = tarfile.TarFile.open(pkg)
        filenames = expand(*filenames, accept_pipe=False)
        if filenames:
            for filename in filenames:
                tf.extract(filename)
                rv.append(filename)
        else:
            tf.extractall()
    elif "-c" in opts:
        if pkg.endswith(".bz2"):
            mode = "w:bz2"
        elif pkg.endswith(".gz"):
            mode = "w:gz"
        else:
            mode = "w"
        tf = tarfile.TarFile.open(pkg, mode)
        filenames = expand(*filenames, accept_pipe=False).splitlines()
        for filename in filenames:
            tf.add(filename)
        tf.close()
    return "\n".join(rv)

def unzip(*args):
    """unzip [-l] [-d DEST] PKG [FILE...]
    extract all or FILEs from PKG to DEST"""
    opts, filenames = _getopts(args, "ld:")
    filenames = expand(*filenames, min=1).splitlines()
    rv = []
    if "-d" in opts:
        dest_dir = opts["-d"]
    else:
        dest_dir = os.getcwd()
    if "-l" in opts:
        # only list files in archive
        for filename in filenames:
            for zi in zipfile.ZipFile(filename).infolist():
                rv.append("%8s  %s  %s" % (
                    zi.file_size,
                    datetime.datetime(*zi.date_time).strftime("%Y-%m-%d %H:%M"),
                    zi.filename))
    else:
        pkg, extract_files = filenames[0], filenames[1:]
        zf = zipfile.ZipFile(pkg)
        if extract_files:
            for extract_file in extract_files:
                zf.extract(extract_file,path=dest_dir)
                rv.append(extract_file)
        else:
            zf.extractall(path=dest_dir)
            rv.extend(zf.namelist())
    return "\n".join(rv)

def xargs(*args):
    """xargs CMD
    run CMD with args from stdin"""
    if not args:
        raise ValueError("xargs: CMD missing")
    if not _g_pipe_has_data:
        raise ValueError("xargs: no get arguments in pipe")
    retval = []
    for arg in open(_g_pipe_filename):
        arg = arg.strip()
        funccall = args[0] + repr(tuple(args[1:]) + (arg,))
        try:
            func_rv = eval(funccall)
            if func_rv and not func_rv.endswith("\n"):
                func_rv += "\n"
            retval.append(func_rv)
        except Exception, e:
            retval.append(str(e).splitlines()[-1] + "\n")
    return "".join(retval)

def xxd(*args):
    """xxd [FILE...]
    make a hexdump"""
    all_files = expand(*args).splitlines()
    rv = []
    for filename in all_files:
        addr = 0
        f = file(filename, "rb")
        while True:
            data16 = f.read(16)
            if len(data16) == 0:
                break
            hex_line = []
            hex_line.append(("%x" % (addr,)).zfill(8) + ": ")
            for bindex, byte in enumerate(data16):
                hex_line.append(("%x" % (ord(byte),)).zfill(2))
                if bindex & 1 == 1:
                    hex_line.append(" ")
            s_hex_line = "".join(hex_line)
            s_hex_line += " " * (51 - len(s_hex_line))
            ascii_line = []
            for byte in data16:
                if 32 <= ord(byte) <= 126:
                    ascii_line.append(byte)
                else:
                    ascii_line.append(".")
            rv.append(s_hex_line + "".join(ascii_line))
            addr += 16
    return "\n".join(rv)

def zip(zipfilename, *filenames):
    """zip ZIPFILE [FILE...]
    add FILEs to ZIPFILE"""
    filenames = expand(*filenames, accept_pipe=False, min=1).splitlines()
    zf = zipfile.ZipFile(zipfilename, "a")
    for filename in filenames:
        zf.write(filename)
    zf.close()
    return ""

def exit():
    if os.name == "nt":
        raise Exception("Close connection with Ctrl-Z + Return")
    else:
        raise Exception("Close connection with Ctrl-D")

def pycosh_eval(cmdline):
    if _g_pspycosh_conn:
        return _g_pspycosh_conn.eval_("pycosh_eval(%s)" % (repr(cmdline,)))
    funccall = cmd2py(cmdline)
    try:
        retval = eval(funccall)
    except Exception, e:
        retval = str(e).splitlines()[-1]
    return retval

def _main():
    histfile = os.path.join(os.path.expanduser("~"), ".pycosh_history")
    try:
        import readline
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass
        atexit.register(readline.write_history_file, histfile)
    except (ImportError, IOError):
        pass

    while True:
        try:
            cmdline = raw_input(pycosh_eval("prompt"))
        except EOFError:
            cmdline = None

        if cmdline == None:
            break
        else:
            cmdline = cmdline.replace("\\", "\\\\")

        if cmdline.strip() == "":
            retval = ""
        else: # run cmdline
            retval = pycosh_eval(cmdline)
        _output(str(retval))

if "__file__" in globals() and __file__.endswith("pycosh.py"):
    _g_pycosh_source = open(__file__, "r").read()

if "_g_pycosh_source" in globals():
    _g_pycosh_source = "_g_pycosh_source = %s\n%s" % (repr(_g_pycosh_source), _g_pycosh_source)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        _main()
    else:
        for cmdline in sys.argv[1:]:
            _output(pycosh_eval(cmdline))
