#!/usr/bin/env python

import glob
import time
import subprocess

from distutils.core import setup

try:
    git_hash = subprocess.check_output(["git", "describe", "--always"]).strip()
except:
    git_hash = "_"
try:
    timestamp = subprocess.check_output(["tinytime", "epoch"]).strip()[:3]
except:
    timestamp = "zzz"

setup(name         = 'autodebug',
      version      = '0.%s.g%s' % (timestamp, git_hash),
      description  = 'gdb-based verbose backtrace printer',
      author       = 'Antti Kervinen',
      author_email = 'antti.kervinen@intel.com',
      packages     = [],
      scripts      = [f for f in glob.glob("bin/*")
                      if not f.endswith("~")]
)
