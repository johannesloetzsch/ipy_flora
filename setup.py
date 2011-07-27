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
      licence='GPL',
      platforms='should be platform-independent — when you have all dependencies (see INSTALL)',
      url='https://github.com/johannesloetzsch/ipy_flora',
      author='Johannes Lötzsch',
      author_email='github_donotspam_at_johannesloetzsch.de',
      description = open('README').readline().strip(),
      long_description = ''.join(open('README').readlines()[1:]).strip(),
      py_modules = [ 'ipy_flora.rpsimple', 'ipy_flora.ipy_flora' ]
	 )

"""test if everything works"""
print
subprocess.call('./test_and_tutorial.py')
