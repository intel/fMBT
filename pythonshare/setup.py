#!/usr/bin/env python

from distutils.core import setup

setup(name         = 'pythonshare',
      version      = '0.1',
      description  = 'Persistent, shared and distributed Python namespaces',
      author       = 'Antti Kervinen',
      author_email = 'antti.kervinen@intel.com',
      packages     = ['pythonshare'],
      scripts      = ['pythonshare-client', 'pythonshare-server'],
      package_data = {'pythonshare': ['__init__.py',
                                      'client.py',
                                      'messages.py',
                                      'server.py']}
)
