#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

import time
import gtk, gobject
from calendarwindow import CalendarWindow
import helpers

class EventEditDialog(gtk.Dialog):
	def __init__(self, parent, evt=None):
		super(EventEditDialog, self).__init__(
			title='Edit Event',
			parent = parent,
			flags=gtk.DIALOG_DESTROY_WITH_PARENT | 
				gtk.DIALOG_NO_SEPARATOR,
			buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, 
				gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		self.vbox.set_spacing(5)

		datebutt = gtk.Button()
		self.h_spin = helpers.spin_button(23)
		self.m_spin = helpers.spin_button(59)
		self.s_spin = helpers.spin_button(59)

		frame = gtk.Frame("Date & Time")
		table = gtk.Table()
		table.set_row_spacings(5)
		table.set_col_spacings(5)
		table.set_border_width(5)
		table.attach(datebutt, 0,3, 0,1)
		table.attach(self.h_spin, 0,1, 1,2)
		table.attach(self.m_spin, 1,2, 1,2)
		table.attach(self.s_spin, 2,3, 1,2)
		frame.add(table)
		self.vbox.pack_start(frame, False)

		self.titlentry = gtk.Entry()
		self.textentry = gtk.TextBuffer()
		textview = gtk.TextView(self.textentry)

		scrolled = gtk.ScrolledWindow()
		scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled.set_shadow_type(gtk.SHADOW_IN)
		scrolled.add(textview)
		table = gtk.Table()
		table.set_row_spacings(5)
		table.set_col_spacings(5)
		table.set_border_width(5)
		table.attach(gtk.Label("Title"), 0,1, 0,1, gtk.SHRINK, gtk.SHRINK)
		table.attach(gtk.Label("Text"), 0,1, 1,2, gtk.SHRINK, gtk.SHRINK)
		table.attach(self.titlentry, 1,2, 0,1, yoptions=gtk.SHRINK)
		table.attach(scrolled, 0,2, 2,3)
		frame = gtk.Frame("Description")
		frame.add(table)
		self.vbox.pack_start(frame, True)

		self.sound = gtk.CheckButton("Sound")
		self.notify = gtk.CheckButton("Notification")

		box = gtk.HBox(True, 5)
		box.pack_start(self.sound)
		box.pack_start(self.notify)
		frame = gtk.Frame("Alarm")
		frame.add(box)

		self.vbox.pack_start(frame, False)

		if evt:
			t = time.localtime(evt[0])
			self.titlentry.set_text(evt[1])
			self.textentry.set_text(evt[2])
			self.sound.set_active(evt[3])
			self.notify.set_active(evt[4])
		else:
			t = time.localtime()
		datebutt.set_label(time.strftime("%x", t))
		self.h_spin.set_value(t.tm_hour)
		self.m_spin.set_value(t.tm_min)
		self.s_spin.set_value(t.tm_sec)
		
		self.date = t[0:3]
		
		datebutt.connect("clicked", self.open_cal)
		self.m_spin.connect("wrapped", self.wrap_spin, self.h_spin)
		self.s_spin.connect("wrapped", self.wrap_spin, self.m_spin)
		#commbutt.connect("clicked", self.try_command, self.commentry)
		self.vbox.show_all()
		#self.show_all()
		
	def wrap_spin(self, sp1, sp2):
		rng = sp1.get_range()
		if sp1.get_value() == rng[0]:	#going up
			sp2.spin(gtk.SPIN_USER_DEFINED, 1)
		elif sp1.get_value() == rng[1]:	#going down
			sp2.spin(gtk.SPIN_USER_DEFINED, -1)

	def open_cal(self, button):
		cw = CalendarWindow(self, self.date)
		cw.connect('day-selected', self.day_selected, button)

	def day_selected(self, cw, date, button):
		self.date = date	# (%Y, %m, %d)
		datestr = time.strftime('%x', date + (0,0,0,0,0,-1))
		button.set_label(datestr)

	def get_event(self):
		tt = [self.date[0], self.date[1], self.date[2],
			self.h_spin.get_value_as_int(), 
			self.m_spin.get_value_as_int(), 
			self.s_spin.get_value_as_int(),
			0, 0, -1]
		text = self.textentry.get_text(self.textentry.get_start_iter(), self.textentry.get_end_iter())
		evt = ( int(time.mktime(tt)),
				self.titlentry.get_text(),
				text,
				self.sound.get_active(),
				self.notify.get_active() )
		return evt

def _test():
	eed = EventEditDialog(parent=None)
	eed.connect('response', _test_response)
	eed.connect('destroy', gtk.main_quit)
	eed.show()
	gtk.main()

def _test_response(win, response):
	for j in win.get_event(): print j
	win.destroy()

if __name__ == '__main__':
	_test()
