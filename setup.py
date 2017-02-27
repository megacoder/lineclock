#!/usr/bin/env python

import shutil
from distutils.core import setup

shutil.copyfile('lineclock.py', 'lineclock/lineclock')

setup(name='lineclock',
	version='0.2.1',
	description='Line desktop clock',
	author='Illia Korchemkin',
	author_email='gm.illifant@gmail.com',
	url='http://code.google.com/p/lineclock/',
	requires = ['pygtk', 'pynotify'],
	license = 'GNU GPL v3',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: X11 Applications',
		'Intended Audience :: End Users/Desktop',
		'License :: GNU General Public License (GPL)',
		'Operating System :: Linux',
		'Programming Language :: Python',
		'Topic :: Desktop'
		],
	packages=['lineclock'],
	scripts=['lineclock/lineclock'],
	data_files = [('share/lineclock', ['lineclock.conf', 'lineclock.gtkrc'])]
	)
