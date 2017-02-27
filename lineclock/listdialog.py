#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

import gtk, gobject, time

class EventList(object):
	def __init__(self, model, parent_window, start_edit_func):
		self.start_edit_func = start_edit_func
		self.window = gtk.Window()
		self.window.set_transient_for(parent_window)
		self.window.set_destroy_with_parent(True)
		self.window.set_title("Events List")

		accel = gtk.AccelGroup()
		self.window.add_accel_group(accel)

		self.actiongroup = gtk.ActionGroup("ListActions")
		self.actiongroup.add_actions([
			("Add", gtk.STOCK_ADD, "New Event", "<Ctrl>n", "Add New Event", self.new_event),
			("Edit", gtk.STOCK_EDIT, "Edit Event", "<Ctrl>e", "Edit Selected Event", self.edit_event),
			("Del", gtk.STOCK_REMOVE, "Remove Event", "Delete", "Remove Selected Event", self.remove_event)
			])
		for action in self.actiongroup.list_actions():
			action.set_accel_group(accel)

		self.treeview = gtk.TreeView(model)
		self.treeview.set_rules_hint(True)

		cell = gtk.CellRendererText()
		cell.set_property("foreground", 'gray')
		col = gtk.TreeViewColumn("Time", cell)
		col.set_cell_data_func(cell, self.cell_time)
		col.set_sort_column_id(0)
		col.set_resizable(True)
		self.treeview.append_column(col)
		col.clicked()

		col = gtk.TreeViewColumn("Title", cell)
		col.set_attributes(cell, text=1)
		col.set_sort_column_id(1)
		col.set_resizable(True)
		self.treeview.append_column(col)

		cell = gtk.CellRendererToggle()
		col = gtk.TreeViewColumn("Snd", cell)
		col.set_attributes(cell, active=3)
		self.treeview.append_column(col)

		col = gtk.TreeViewColumn("Notify", cell)
		col.set_attributes(cell, active=4)
		self.treeview.append_column(col)

		scrollwin = gtk.ScrolledWindow()
		scrollwin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrollwin.add(self.treeview)
		scrollwin.set_shadow_type(gtk.SHADOW_IN)

		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
		self.menu = gtk.Menu()
		for act_name in ["Add", "Edit", "Del"]:
			action = self.actiongroup.get_action(act_name)
			menuitem = action.create_menu_item()
			toolitem = action.create_tool_item()
			self.menu.append(menuitem)
			toolbar.insert(toolitem, -1)

		self.menu.show_all()

		vbox = gtk.HBox()
		vbox.pack_start(toolbar, False)
		vbox.pack_start(scrollwin, True)
		vbox.show_all()
		self.window.add(vbox)

		self.treeview.connect('row-activated', self.tree_row_activated)
		self.treeview.connect('button_press_event', self.popup_menu)
		self.window.connect('delete-event', self.on_delete_window)

	def cell_time(self, col, cell, model, iter):
		t = model.get_value(iter, 0)
		tx = time.strftime("%X %x", time.localtime(t))
		cell.set_property("text", tx)
		now = time.time()
		cell.set_property("foreground-set", t<now)

	def new_event(self, w):
		print "new event call"
		self.edit_event(None, True)

	def tree_row_activated(self, tree, path, col):
		print "tree row activated call"
		self.edit_event(None, False)

	def edit_event(self, w, new=False):
		model, iter = self.treeview.get_selection().get_selected()
		if new or not iter:
			evt = (int(time.time()), '', '', True, True)
			iter = None
		elif iter:
			evt = model.get(iter, *range(5))
		self.start_edit_func(evt, iter)

	def remove_event(self, w):
		print "remove evt call"
		model, iter = self.treeview.get_selection().get_selected()
		if iter:
			model.remove(iter)

	def on_delete_window(self, w, e):
		self.window.hide()
		return self.window.get_transient_for()
	
	def popup_menu(self, w, event):
		if event.button == 3:
			self.menu.popup(None, None, None, event.button, event.time)

def _test():
	model = gtk.ListStore(int, str, str, bool, bool)
	model.append((time.time(), 'whatever', 'omg screw you all', False, True))
	model.append((time.time()+60, 'fhtagn', 'omg screw you all', True, True))
	model.append((time.time()-60, 'ololo', 'omg screw you all', True, False))
	def sef(e,i): print e
	el = EventList(model, None, sef)
	el.window.resize(300, 200)
	el.window.show_all()
	el.window.connect('destroy',gtk.main_quit)
	gtk.main()

if __name__ == '__main__':
	_test()
