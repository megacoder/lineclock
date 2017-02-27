#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

import time, gtk, gobject

class CalendarWindow(gobject.GObject):
	__gsignals__ = {'day-selected': (gobject.SIGNAL_RUN_LAST,
			gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)) }
	def __init__(self, parent, date=None):
		super(CalendarWindow, self).__init__()
		W = gtk.Window()
		W.set_decorated(False)
		W.set_skip_taskbar_hint(True)
		W.set_skip_pager_hint(True)
		W.set_transient_for(parent)
		W.set_destroy_with_parent(True)
		W.set_position(gtk.WIN_POS_MOUSE)

		self.calendar = gtk.Calendar()
		self.calendar.mark_day(time.localtime().tm_mday)

		if date:
			self.calendar.select_month(date[1]-1, date[0])
			self.calendar.select_day(date[2])

		self.calendar.connect('focus-out-event', self._cancelled)
		self.calendar.connect('month-changed', self._month_changed)
		self.calendar.connect('day-selected-double-click', self._day_selected)
		self.calendar.connect('key-press-event', self._day_selected)

		W.add(self.calendar)
		W.show_all()

	def _cancelled(self, cal, evt):
		cal.get_toplevel().destroy()

	def _month_changed(self, cal):
		now_date = time.localtime()
		cal_date = cal.get_date()
		if now_date[0] == cal_date[0] and now_date[1] == cal_date[1]+1:
			cal.mark_day(now_date[2])
		else:
			cal.clear_marks()

	def _day_selected(self, cal, evt=None):
		if not evt or evt.type == gtk.gdk.KEY_PRESS and gtk.gdk.keyval_name(evt.keyval) == 'Return':
			year, month, day = cal.get_date()
			self.emit('day-selected', (year, month+1, day))
			cal.get_toplevel().destroy()
		elif evt.type == gtk.gdk.KEY_PRESS and gtk.gdk.keyval_name(evt.keyval) == 'Escape':
			cal.get_toplevel().destroy()

def _test():
	W = gtk.Window()
	B = gtk.Button()
	W.add(B)
	B.connect('clicked', _test_button_click)
	W.connect('destroy', gtk.main_quit)
	W.resize(100,50)
	W.show_all()
	gtk.main()

def _test_button_click(B):
	cw = CalendarWindow(B.get_toplevel())
	cw.connect('day-selected', _test_cw_response, B)

def _test_cw_response(cw, date, B):
	datestr = time.strftime('%x', (date[0], date[1]+1, date[2], 0,0,0,0,0,-1))
	print datestr
	B.set_label(datestr)

if __name__ == '__main__':
	_test()
