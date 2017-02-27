#!/usr/bin/env python
#
#       lineclock.py
#       
#       Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import os, sys

FAIL = False
if sys.version_info < (2, 5):
	sys.stderr.write('Python 2.5 or more is required\n')
	FAIL = True

try:	# these modules are usually shipped with pygtk
	import gtk, gobject, cairo, pango
	if gtk.pygtk_version < (2, 12, 0):
		raise Exception
except:
	sys.stderr.write('Pygtk 2.12.0 or more is required. Exiting\n')
	FAIL = True

try:
	import pynotify
except:
	sys.stderr.write('pynotify module is required. Exiting\n')
	FAIL = True

try:
	import lineclock
except:
	sys.stderr.write('Cannot find lineclock module\n')
	sys.stderr.write("\nSearched in the following directories:\n" +
             "\n".join(sys.path) + "\n")
	FAIL = True

# collect all errors, only then exit
if FAIL:
	sys.exit(1)

from lineclock.main import LineClock
LineClock()
gtk.main()
