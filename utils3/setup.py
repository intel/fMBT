#!/usr/bin/env python3

from distutils.core import setup, Extension
import os
import shutil
import subprocess
import sys

def check_output(*args):
    """subprocess.check_output, for Python 2.6 compatibility"""
    p = subprocess.Popen(*args, stdout=subprocess.PIPE)
    out, err = p.communicate()
    exitstatus = p.poll()
    if exitstatus:
        raise subprocess.CalledProcessError(exitstatus, args[0])
    return out.decode('utf-8')

def pkg_config(package):
    if os.name == "nt":
        if package == "MagickCore":
            # pkg-config cannot be used, try to find needed libraries from the filesystem
            import fnmatch
            libraries = ["CORE_RL_magick_"]
            library_dirs = []
            include_dirs = []
            missing_libs = set(["kernel32.lib"] + [l + ".lib" for l in libraries])
            missing_headers = set(["magick/MagickCore.h"])
            for rootdir, dirnames, filenames in os.walk(os.environ["ProgramFiles"]):
                for library in sorted(missing_libs):
                    if fnmatch.filter(filenames, library) and not "x64" in rootdir:
                        library_dirs.append(rootdir)
                        missing_libs.remove(library)
                        if not missing_libs:
                            break
                for header in missing_headers:
                    if fnmatch.filter(filenames, os.path.basename(header)):
                        if os.path.dirname(header) == "":
                            include_dirs.append(rootdir)
                        elif os.path.dirname(header) == os.path.basename(rootdir):
                            include_dirs.append(os.path.dirname(rootdir))
                        missing_headers.remove(header)
                        if not missing_headers:
                            break
                if not missing_libs and not missing_headers:
                    break
            ext_args = {
                "libraries": libraries,
                "library_dirs": sorted(set(library_dirs)),
                "include_dirs": include_dirs,
            }
        else:
            sys.stderr.write('Unknown build parameters for package "%s"\n' % (package,))
            sys.exit(1)
    else:
        _pkg_config = os.getenv("PKG_CONFIG","pkg-config")
        o = check_output([_pkg_config, "--libs", "--cflags", package])
        ext_args = {"libraries": [], "library_dirs": [], "include_dirs": [], "extra_compile_args": []}
        for arg in o.split():
            if arg.startswith("-L"):
                ext_args["library_dirs"].append(arg[2:])
            elif arg.startswith("-l"):
                ext_args["libraries"].append(arg[2:])
            elif arg.startswith("-I"):
                ext_args["include_dirs"].append(arg[2:])
            else:
                ext_args["extra_compile_args"].append(arg)
    return ext_args

fmbt_utils_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),os.getenv("VPATH",""))
fmbt_dir = os.path.join(fmbt_utils_dir, "..")

version = (open(os.path.join(fmbt_dir, "configure.ac"), "r")
           .readline()
           .split(",")[1]
           .replace(' ','')
           .replace('[','')
           .replace(']',''))

lines = [line.replace("\\","").strip()
         for line in open(os.path.join(fmbt_utils_dir, "Makefile.am"))
         if not "=" in line]

modules = [module.replace(".py","")
           for module in lines[lines.index("# modules")+1:
                               lines.index("# end of modules")]]

scripts = lines[lines.index("# scripts")+1:
                lines.index("# end of scripts")]

ext_modules = []
if os.getenv("with_imagemagick", "yes").lower() != "no":
    if not os.path.isfile("./eye4graphics.cc"):
        shutil.copy("../utils/eye4graphics.cc", "./eye4graphics.cc")
    if not os.path.isfile("./eye4graphics.h"):
        shutil.copy("../utils/eye4graphics.h", "./eye4graphics.h")
    eye4graphcs_buildflags = pkg_config("MagickCore")
    ext_eye4graphics = Extension('eye4graphics',
                                 sources = ['eye4graphics.cc'],
                                 **eye4graphcs_buildflags)
    ext_modules.append(ext_eye4graphics)

setup(name         = 'fmbt-python',
      version      = version,
      description  = 'fMBT Python tools and libraries',
      author       = 'Antti Kervinen',
      author_email = 'antti.kervinen@intel.com',
      py_modules   = modules,
      scripts      = scripts,
      ext_modules  = ext_modules
  )
