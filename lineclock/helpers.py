#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

import os, sys
import gtk
import ConfigParser

class SMConfParser(ConfigParser.SafeConfigParser):
	"""ConfigParser with getting tuples"""
	def gettuple(self, section, option, length):
		row = self.get(section, option)
		result = tuple(float(x) for x in row.strip('()[]').split(','))
		if len(result) == length:
			return result
		else:
			raise ValueError('Wrong tuple length')

def image_menu_item(label, stock_id):
	item = gtk.ImageMenuItem(label)
	item.set_image(gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU))
	return item

def spin_button(highest):
	spin = gtk.SpinButton()
	spin.set_increments(1,5)
	spin.set_range(0,highest)
	spin.set_numeric(True)
	spin.set_wrap(True)
	return spin

def find_path(filename):
	full_filename = None
	possible_names = [
		os.path.normpath(os.path.join(os.path.split(__file__)[0], '..', filename)),
		os.path.join(__file__.split('/lib')[0], 'share', 'lineclock', filename),
		os.path.join(sys.prefix, 'share', 'lineclock', filename) 
	]
	for n in possible_names:
		if os.path.exists(n):
			full_filename = n
			break
	if not full_filename:
		raise Exception(filename + " cannot be found")
	return full_filename
