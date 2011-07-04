#!/usr/bin/python
# -*- coding: utf-8 -*-
"""To install run this script with root-privileges"""

import sys
from distutils.core import setup
import subprocess

"""installation using python-distutils"""
sys.argv.append('install')
setup(name='ipy_flora',
      version='0.1',
      url='https://github.com/johannesloetzsch/ipy_flora',
      author='Johannes Lötzsch',
      author_email='github_donotspam_at_johannesloetzsch.de',
      py_modules = [ 'ipy_flora.rpsimple', 'ipy_flora.ipy_flora' ]
	 )

"""test if everything works"""
print
subprocess.call('./test_and_tutorial.py')
