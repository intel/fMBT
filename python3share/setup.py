#!/usr/bin/env python3

from distutils.core import setup

setup(name         = 'python3share',
      version      = '0.42',
      description  = 'Persistent, shared and distributed Python 3 namespaces',
      author       = 'Antti Kervinen',
      author_email = 'antti.kervinen@intel.com',
      packages     = ['python3share'],
      scripts      = ['python3share-client', 'python3share-server'],
      package_data = {'python3share': ['__init__.py',
                                      'client.py',
                                      'messages.py',
                                      'server.py']}
)
