#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

import ConfigParser, time, cPickle, os, sys
import gtk, gobject
import pynotify
from widget import HLineClockWidget, VLineClockWidget
from editdialog import EventEditDialog
import helpers
from listdialog import EventList

class LineClock():
	def __init__(self):
		self.window = gtk.Window()
		self.window.set_title("Lineclock")

		self.load_config()	# this also creates H or V LCWidget

		self.menu = gtk.Menu()
		self.item_new = helpers.image_menu_item("Add Event Here", gtk.STOCK_ADD)
		self.item_edit = helpers.image_menu_item("Edit this Event", gtk.STOCK_EDIT)
		self.item_remove = helpers.image_menu_item("Remove this Event", gtk.STOCK_REMOVE)
		item_list = helpers.image_menu_item("Events List", gtk.STOCK_INDEX)
		item_reread = helpers.image_menu_item("Reload Config", gtk.STOCK_PREFERENCES)
		item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		for item in [self.item_new, self.item_edit, self.item_remove, item_list,
			gtk.SeparatorMenuItem(), item_reread, gtk.SeparatorMenuItem(), item_quit]:
				self.menu.append(item)
		self.menu.show_all()

		#								time title text sound notify
		self.event_store = gtk.ListStore(int, str, str, bool, bool)
		self.event_list = None
		self.here_time_function = time.time
		self.event_menu_on = None
		self._setup_widget()

		self.window.connect('delete_event', self.quit)
		self.item_new.connect('activate', self.new_event_here)
		self.item_edit.connect('activate', self.edit_this_event)
		self.item_remove.connect('activate', self.remove_this_event)
		item_list.connect('activate', self.show_event_list)
		item_reread.connect('activate', self.reread_config_callback)
		item_quit.connect('activate', self.quit)
		self.event_store.connect('row-changed',self.reset_markers)
		self.event_store.connect('row-deleted',self.reset_markers)
		self.event_store.connect('row-inserted',self.reset_markers)
		self.widget.connect('query-tooltip', self.show_tooltip)
		self.widget.connect('alarm', self.alarm)
		self.load_events()
		self.window.show()

	def load_config(self):
		try:
			default_config = helpers.find_path("lineclock.conf") # this MUST be complete config with ALL options
		except Exception, e:
			print e
			sys.exit(1)
		user_config = os.path.expanduser("~/.config/lineclock/lineclock.conf")
		conf = helpers.SMConfParser()
		conf.readfp(open(default_config))
		conf.read(user_config)

		w_type = conf.get('widget','type')

		if not hasattr(self, 'widget'):	 # on startup we have no widget
			self.widget = (HLineClockWidget, VLineClockWidget)[w_type == 'V']()
		elif self.widget.type != w_type:
			self._change_type()

		for attr in ['timerange', 'nowrel', 'tickgap', 'main_w', 'long_w', 'short_w', 'now_w', 'marker_w', 'label_x', 'label_y', 'pos_tolerance']:
			setattr(self.widget, attr, conf.getfloat('widget', attr))
		for attr in ['ntick', 'ltr']:
			setattr(self.widget, attr, conf.getint('widget', attr))
		for attr in ['long_h', 'short_h', 'now_h', 'marker_h']:
			setattr(self.widget, attr, conf.gettuple('widget', attr, 2))
		self.widget.label_fmt = conf.get('widget', 'label_fmt', raw=True)

		self.rc_file = conf.get('widget', 'gtkrc')
		if not self.rc_file:
			try:
				self.rc_file = helpers.find_path("lineclock.gtkrc")
			except: pass
		gtk.rc_parse(os.path.expanduser(self.rc_file))
		gtk.rc_reset_styles(gtk.settings_get_default())

		# Window props
		self.window.set_decorated(conf.getboolean('window', 'decorated'))
		self._keep_below = conf.getboolean('window', 'keep_below')
		self.window.set_keep_below(self._keep_below)	# bug with gdk.Window.get_state()
		self.window.set_skip_pager_hint(conf.getboolean('window', 'skip_pager'))
		self.window.set_skip_taskbar_hint(conf.getboolean('window', 'skip_taskbar'))
		if conf.getboolean('window', 'sticky'):
			self.window.stick()
			self._sticky = True
		else:
			self.window.unstick()
			self._sticky = False
		x = conf.getint('window', 'x')
		y = conf.getint('window', 'y')
		self.window.move(x, y)
		wlen = conf.getint('window', 'length')
		(ww, wh) = self.widget.size_request()
		if self.widget.type == 'H':
			self.window.set_geometry_hints(max_width=gobject.G_MAXINT, max_height=wh)
			des_size = (wlen, wh)
		else:
			self.window.set_geometry_hints(max_height=gobject.G_MAXINT, max_width=ww)
			des_size = (ww, wlen)
		gobject.idle_add(self.window.resize, *des_size)
		self.window.set_opacity(conf.getfloat('window', 'opacity'))

		# misc
		self.tooltip_fmt = conf.get('misc', 'tooltip_fmt', raw=True)

		#alarm
		self.sound_player = conf.get('alarm', 'player', raw=True)
		self.sound_file = conf.get('alarm', 'file', raw=True)

	def save_config(self):
		user_config = os.path.expanduser("~/.config/lineclock/lineclock.conf")
		if not os.path.isdir(os.path.expanduser("~/.config/lineclock")):
			try:
				os.makedirs(os.path.expanduser("~/.config/lineclock"), 0750)
			except OSError, e:
				print e
				return
		try:
			f = open(user_config, 'w')
		except IOError,e:
			print e
			return
		conf = ConfigParser.ConfigParser()
		conf.add_section('widget')
		for attr in ['type', 'timerange', 'nowrel', 'tickgap', 'main_w',
			'long_w', 'short_w', 'now_w', 'marker_w', 'label_x', 'label_y',
			'ntick', 'ltr', 'long_h', 'short_h', 'now_h', 'marker_h',
			'pos_tolerance']:
				conf.set('widget', attr, str(getattr(self.widget, attr)))
		conf.set('widget', 'label_fmt', self.widget.label_fmt)
		conf.set('widget', 'gtkrc', self.rc_file)
		
		conf.add_section('window')
		conf.set('window', 'decorated', str(self.window.get_decorated()))
		conf.set('window', 'skip_pager', str(self.window.get_skip_pager_hint()))
		conf.set('window', 'skip_taskbar', str(self.window.get_skip_taskbar_hint()))
		x, y = self.window.get_position()
		conf.set('window', 'x', str(x))
		conf.set('window', 'y', str(y))
		wlen = self.window.get_size()[self.widget.type == 'V']
		conf.set('window', 'length', str(wlen))
		conf.set('window', 'opacity', str(self.window.get_opacity()))		
		#if self.window.window: # does not work. window state is never STATE_BELOW or STATE_ABOVE. GTK bug?
			#state = self.window.window.get_state()
			#keep_below = bool(state & gtk.gdk.WINDOW_STATE_BELOW)
			#sticky = bool(state & gtk.gdk.WINDOW_STATE_STICKY)
		#else:
			#sticky = False
		conf.set('window', 'keep_below', str(self._keep_below))
		conf.set('window', 'sticky', str(self._sticky))

		conf.add_section('misc')
		conf.set('misc', 'tooltip_fmt', self.tooltip_fmt)
		
		conf.add_section('alarm')
		conf.set('alarm', 'player', self.sound_player)
		conf.set('alarm', 'file', self.sound_file)
	
		conf.write(f)

	def reread_config_callback(self, w):
		self.load_config()

	def quit(self, *args):
		self.save_config()
		self.save_events()
		gtk.main_quit()

	def _setup_widget(self):
		self.window.add(self.widget)
		self.widget.show()
		self.widget.props.has_tooltip = True
		self.widget.add_events(gtk.gdk.BUTTON_PRESS_MASK)
		self.widget.connect('button_press_event', self.popup_menu)
		self.timeout = gobject.timeout_add(1000, self.widget.update)

	def _change_type(self):
		gobject.source_remove(self.timeout)
		oldtype = self.widget.type
		self.window.remove(self.widget)
		self.widget = (HLineClockWidget, VLineClockWidget)[oldtype == 'H'](self.widget)
		self._setup_widget()

	def popup_menu(self, widget, event):
		if event.button == 3:
			pos = (event.x, event.y)
			self.here_time_function = lambda: self.widget.pos_to_time(pos)
			self.event_menu_on = self.widget.pos_on_marker(pos)
			if self.event_menu_on:
				self.item_new.hide()
				self.item_edit.show()
				self.item_remove.show()
			else:
				self.item_new.show()
				self.item_edit.hide()
				self.item_remove.hide()
			self.menu.popup(None, None, None, event.button, event.time)

	def new_event_here(self, w):
		here_time = self.here_time_function()
		evt = (int(here_time), '', '', True, True)
		self.start_edit_dialog(evt)
		self.here_time_function = time.time

	def edit_this_event(self, w):
		iter = self.find_event(self.event_menu_on)
		if iter:
			evt = self.event_store.get(iter, *range(5))
			self.start_edit_dialog(evt, iter)

	def start_edit_dialog(self, evt, iter=None):
		eed = EventEditDialog(self.window, evt)
		eed.connect('response', self.edit_dialog_response, iter)
		eed.show()

	def remove_this_event(self, w):
		iter = self.find_event(self.event_menu_on)
		if iter: self.event_store.remove(iter)

	def find_event(self, marker):
		iter = self.event_store.get_iter_first()
		while iter:
			if self.event_store.get_value(iter, 0) == marker:
				return iter
			iter = self.event_store.iter_next(iter)
		return None

	def edit_dialog_response(self, win, response, iter=None):
		if response == gtk.RESPONSE_ACCEPT:
			evt = win.get_event()
			print evt
			if iter:
				self.event_store.set(iter, *sum(enumerate(evt), ()))
			else:
				self.event_store.append(evt)
		win.destroy()

	def show_event_list(self, w):
		if not self.event_list:
			self.event_list = EventList(self.event_store, self.window, self.start_edit_dialog)
			self.event_list.window.resize(300, 200)
		self.event_list.window.present()

	def reset_markers(self, model, path=None, iter=None):
		self.widget.markers = [r[0] for r in model]

	def show_tooltip(self,	widget, x, y, keyboard_tip, tooltip):
		mark = widget.pos_on_marker((x, y))
		if mark:
			iter = self.find_event(mark)
			evt = self.event_store.get(iter, *range(5))
		elif abs(widget.pos_to_time((x, y)) - time.time()) <= \
						widget.pos_tolerance*widget.get_scale():
			evt = (time.time(), 'Now', '')
		else:
			return False
		evtime = time.strftime(self.tooltip_fmt, time.localtime(evt[0]))
		tooltip.set_markup("<b>%s\n%s</b>\n%s" % (evtime, evt[1], evt[2]))
		return True

	def alarm(self, widget, mark):
		iter = self.find_event(mark)
		if iter:
			evt = self.event_store.get(iter, *range(5))
			if evt[3]: self.make_sound()
			if evt[4]: self.make_notification(evt)

	def make_sound(self):
		if not (self.sound_file and os.path.isfile(self.sound_file)):
			print 'No sound file'
			return
		if not self.sound_player:
			print "Sound player isn't set"
			return
		try:
			gobject.spawn_async(self.sound_player.split() + [self.sound_file],
								flags=gobject.SPAWN_SEARCH_PATH)
		except Exception, e:
			print e

	def make_notification(self, evt):
		evtime = time.strftime(self.tooltip_fmt, time.localtime(evt[0]))
		pynotify.init("Markup")
		n = pynotify.Notification("%s\n%s" % (evtime, evt[1]), evt[2])
		n.show()

	def save_events(self):
		if not os.path.isdir(os.path.expanduser("~/.config/lineclock")):
			try:
				os.makedirs(os.path.expanduser("~/.config/lineclock"), 0750)
			except OSError, e:
				print e
				return
		data_file = os.path.expanduser("~/.config/lineclock/data")
		try:
			f = open(data_file, 'w')
		except IOError, e:
			print e
			return
		events = [tuple(r) for r in self.event_store]
		cPickle.dump(events, f)
		f.close()

	def load_events(self):
		data_file = os.path.expanduser("~/.config/lineclock/data")
		try:
			f = open(data_file, 'r')
			events = cPickle.load(f)
		except Exception, e:
			print e
			return
		f.close()
		self.event_store.clear()
		for r in events:
			self.event_store.append(r)

if __name__ == '__main__':
	L = LineClock()
	gtk.main()
