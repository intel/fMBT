#!/usr/bin/env python

from distutils.core import setup, Extension
import os
import subprocess

def pkg_config(package):
    o = subprocess.check_output(["pkg-config", "--libs", "--cflags", package])
    ext_args = {"libraries": [], "library_dirs": [], "include_dirs": [], "extra_compile_args": []}
    for arg in o.split():
        if arg.startswith("-L"):
            ext_args["library_dirs"].append(arg[2:])
        elif arg.startswith("-l"):
            ext_args["libraries"].append(arg[2:])
        elif arg.startswith("-I"):
            ext_args["include_dirs"].append(arg[2:])
        elif arg.startswith("-f"):
            ext_args["extra_compile_args"].append(arg)
        else:
            raise ValueError('Unexpected pkg-config output: "%s" in "%s"'
                             % (arg, o))
    return ext_args

fmbt_utils_dir = os.path.abspath(os.path.dirname(__file__))
fmbt_dir = os.path.join(fmbt_utils_dir, "..")

version = (file(os.path.join(fmbt_dir, "configure.ac"), "r")
           .readline()
           .split(",")[1]
           .replace(' ','')
           .replace('[','')
           .replace(']',''))

lines = [line.replace("\\","").strip()
         for line in file(os.path.join(fmbt_utils_dir, "Makefile.am"))
         if not "=" in line]

modules = [module.replace(".py","")
           for module in lines[lines.index("# modules")+1:
                               lines.index("# end of modules")]]

scripts = lines[lines.index("# scripts")+1:
                lines.index("# end of scripts")]

eye4graphcs_buildflags = pkg_config("Magick++")
ext_eye4graphics = Extension('eye4graphics',
                             sources = ['eye4graphics.cc'],
                             **eye4graphcs_buildflags)

setup(name         = 'fmbt-python',
      version      = version,
      description  = 'fMBT Python tools and libraries',
      author       = 'Antti Kervinen',
      author_email = 'antti.kervinen@intel.com',
      py_modules   = modules,
      scripts      = scripts,
      ext_modules  = [ext_eye4graphics]
  )
