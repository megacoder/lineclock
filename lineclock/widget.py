#!/usr/bin/env python
# this program is part of lineclock
# Copyright 2010 Illia Korchemkin <gm.illifant@gmail.com>

# Module contains LineClockWidget class and HLineClockWidget and 
# VLineClockWidget derived from it
#
# Attributes
# time - seconds from Epoch
# markers - list of times where markers are placed. Default: []
# timerange - range of visible time, seconds. Default: 7200 (2 hours)
# nowrel - normalized position of NOW on the axe. Default: 0.5
# tickgap - time between labeled ticks, seconds. Default: 3600
# ntick - number of ticks between labeled ones. Default: 4
# ltr - +1 if time raises left-to-right / top-to-bottom. -1 otherwise
# main_w, long_w, short_w, now_w, marker_w - width of lines: time axe, 
#   labeled ticks, simple ticks, NOW line, markers. In pixels
# long_h, short_h, now_h, marker_h - heights of lines. Tuples of length 2.
#   1st component is line's lower end measured from main line downwadrs.
#   2nd component is line's upper end measured from main line downwadrs. negative
# label_x - distance from tick to label's center. Positive is right
# label_y - distance from main line to label's bottom. Positive is upwards
# label_fmt - format string for use in time.strftime
#
# gtkrc parameters in use:
# bg[NORMAL] - background (not used directly since it may be pixmap)
# fg[NORMAL] - main line&ticks	fg[0]
# fg[ACTIVE] - now line			fg[1]
# fg[PRELIGHT] - labels			fg[2] !!! INSENSITIVE, fg[4]
# fg[SELECTED] - markers		fg[3]
# xthickness
# ythickness
# font_name (gets used automatically)
# widget "*lineclock-widget" style...

from __future__ import division
import time
import gtk, gobject, cairo, pango

class LineClockWidget(gtk.DrawingArea):
	"""Base class for HLineClockWidget and VLineClockWidget"""
	__gsignals__ = {"size-request": "override",
					"expose-event": "override",
					"alarm": (gobject.SIGNAL_RUN_FIRST,
							  gobject.TYPE_NONE,
							  (gobject.TYPE_INT,))}
	def __init__(self, proto = None):
		super(LineClockWidget, self).__init__()
		self.set_name('lineclock-widget')

		if proto:
			for attr in ['timerange', '_nowrel', '_shortgap', '_ntick',
				'main_w', 'long_w', 'long_h', 'short_w', 'short_h',
				'now_w', 'now_h', 'marker_w', 'marker_h', '_ltr',
				'label_fmt', 'label_x', 'label_y', 'markers', 'pos_tolerance']:
					setattr(self, attr, getattr(proto, attr))
		else:
			self.timerange = 14400
			self._nowrel = 0.5
			self._shortgap = 600	#between any ticks
			self._ntick = 6			#how many short ticks between long ones
			self.main_w = 4
			self.long_w = 2
			self.long_h = (10, -20)			#from main line. lower,upper end
			self.short_w = 1
			self.short_h = (5, -5)
			self.now_w = 3
			self.now_h = (10, -25)
			self.marker_w = 2
			self.marker_h = (10, -17)
			self.label_fmt = "%H:%M"	#for use in time.strftime
			self.label_y = 0
			self.label_x = 0
			self._ltr = 1	# past is to the left/down. -1 otherwise
			self.markers = []
			self.pos_tolerance = 5

		self._time = int(time.time())
		self._ticklabel = self.create_pango_layout(
			time.strftime(self.label_fmt, time.localtime(self._time)))

	#time is private 'cause there is update after time change
	def _get_time(self):
		return self._time
	def _set_time(self, t):
		self._time = int(t)
		if self.window:
			self.queue_draw_area(*self.get_allocation())
			self.window.process_updates(True)
	time = property(_get_time, _set_time)

	def do_expose_event(self, evt):
		"""expose-event signal handler"""
		ctx = self.window.cairo_create()
		ctx.rectangle(evt.area.x, evt.area.y, evt.area.width, evt.area.height)
		ctx.clip()
		self._draw(ctx)
		return False

	def update(self):
		self.time = time.time()
		for m in self.markers:
			if int(m) == self._time:
				self.emit("alarm", m)
				break
		return True

	def _draw(self, ctx):
		"""dummy method. to be implemented in H or V LCW"""
		pass

	#we want to make public the gap between labeled ticks
	def _get_tickgap(self):
		return self._shortgap*self._ntick
	def _set_tickgap(self, gap):
		if (not isinstance(gap, (int, float))) or gap <= 0:
			raise TypeError, 'tickgap must be a positive integer or float'
		self._shortgap = gap/self._ntick
	tickgap = property(_get_tickgap, _set_tickgap)

	#so ntick must also be private
	def _get_ntick(self):
		return self._ntick
	def _set_ntick(self, n):
		if (not isinstance(n, int)) or n < 1:
			raise TypeError, 'ntick must be a positive integer'
		self._shortgap = self.tickgap/n
		self._ntick = n
	ntick = property(_get_ntick, _set_ntick)

	# if RTL, nowrel is from right edge. inside it's always from left
	def _get_nowrel(self):
		if self.ltr == 1:
			return self._nowrel
		else:
			return 1 - self._nowrel
	def _set_nowrel(self, nr):
		if self.ltr == 1:
			self._nowrel = nr
		else:
			self._nowrel = 1 - nr
	nowrel = property(_get_nowrel, _set_nowrel)

	def _get_ltr(self):
		return self._ltr
	def _set_ltr(self, ltr):
		if ltr not in (-1, 1):
			raise ValueError, 'ltr is either 1 or -1'
		if self._ltr != ltr:
			self._nowrel = 1 - self._nowrel
		self._ltr = int(ltr)
	ltr = property(_get_ltr, _set_ltr)

	def _request_min_max(self, label, font):
		h_max = max(label+font/2, *self.long_h + self.short_h + self.now_h + self.marker_h)
		h_min = min(label+font/2, *self.long_h + self.short_h + self.now_h + self.marker_h)
		self._excenter = (h_max + h_min)/2
		return (h_min, h_max)

	def style_color(self, state):
		color = (self.style.fg[state].red_float,
				 self.style.fg[state].green_float,
				 self.style.fg[state].blue_float)
		return color

	def pos_to_time(self, pos):
		'''returns time on widget's scale with position pos. time is seconds from the Epoch'''
		x = self._norm_pos(pos)
		w = self._length()
		return self._time + (x/w - self._nowrel)*self.timerange*self._ltr

	def get_scale(self):
		'''returns how many seconds in 1 pix'''
		return self.timerange/self._length()

	def pos_on_marker(self, pos):
		tx = self.pos_to_time(pos)
		thres = self.pos_tolerance*self.get_scale()
		for m in self.markers:
			if abs(tx - m) <= thres:
				return m
		return None

class HLineClockWidget(LineClockWidget):
	"""Widget with horizontal time line"""
	type = property(lambda s: 'H')
	def _draw(self, ctx):
		alc = self.get_allocation()
		ctx.translate(alc.x + self.style.xthickness,
					  alc.height/2 - self._excenter)
		width = alc.width - 2*self.style.xthickness

		#MainLain/MineLine
		ctx.move_to(0,0)
		ctx.rel_line_to(width, 0)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
		ctx.set_line_width(self.main_w)
		ctx.stroke()

		#NOW
		ctx.set_line_width(self.now_w)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_ACTIVE))
		ctx.move_to(self._nowrel*width, self.now_h[0])
		ctx.rel_line_to(0, self.now_h[1] - self.now_h[0])
		ctx.stroke()

		#ticks
		#closest long tick before NOW. some number of long ticks after midnight
		# well, who cares if it's time from Epoch or from last midnight?
		t0 = self._time - self._time % self.tickgap
		#it's position
		x0 = (self._nowrel + (t0 - self._time)/self.timerange*self._ltr)*width
		#distance between ticks
		dx = self._shortgap/self.timerange*width
		#how many ticks are below t0
		i = -(x0//dx)
		x0 += i*dx
		t0 += i*self._shortgap*self._ltr
		while x0 <= width:
			if i%self._ntick == 0:		#means long tick
				ctx.move_to(x0, self.long_h[0])
				ctx.line_to(x0, self.long_h[1])
				ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
				ctx.set_line_width(self.long_w)
				ctx.stroke()
				# Labels
				self._ticklabel.set_text(
					time.strftime(self.label_fmt, time.localtime(t0)))
				fontw, fonth = self._ticklabel.get_pixel_size()
				ctx.set_source_rgb(*self.style_color(gtk.STATE_INSENSITIVE))
				ctx.move_to(x0 - 0.5*fontw + self.label_x,
							self.label_y-fonth/2)
				ctx.show_layout(self._ticklabel)
			else:
				ctx.move_to(x0, self.short_h[0])
				ctx.line_to(x0, self.short_h[1])
				ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
				ctx.set_line_width(self.short_w)
				ctx.stroke()
			i += 1
			t0 += self._shortgap*self._ltr
			x0 += dx

		#markers
		ctx.set_line_width(self.marker_w)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_SELECTED))
		for m in self.markers:
			xm = (self._nowrel + (m - self._time)/self.timerange*self._ltr)*width
			if xm > 0 and xm < width:
				ctx.move_to(xm, self.marker_h[0])
				ctx.line_to(xm, self.marker_h[1])
		ctx.stroke()

	def do_size_request(self, req):
		"""size-request signal handler"""
		fw, fh = self._ticklabel.get_pixel_size()
		h_min, h_max = self._request_min_max(self.label_y, fh)
		req.height = 2*self.style.ythickness + h_max - h_min
		req.width  = 2*self.style.xthickness + fw*self.timerange/self.tickgap

	def _length(self):
		return self.get_allocation().width - 2*self.style.xthickness
	def _norm_pos(self, pos):
		return pos[0] - self.style.xthickness

class VLineClockWidget(LineClockWidget):
	"""Widget with vertical time line"""
	type = property(lambda s: 'V')
	def _draw(self, ctx):
		alc = self.get_allocation()
		ctx.translate(alc.width/2 - self._excenter,
					  alc.y + self.style.ythickness)
		height = alc.height - 2*self.style.ythickness

		#MainLain/MineLine
		ctx.move_to(0, 0)
		ctx.rel_line_to(0, height)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
		ctx.set_line_width(self.main_w)
		ctx.stroke()

		#NOW
		ctx.set_line_width(self.now_w)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_ACTIVE))
		ctx.move_to(self.now_h[0], self._nowrel*height)
		ctx.rel_line_to(self.now_h[1] - self.now_h[0], 0)
		ctx.stroke()

		#ticks
		#closest long tick before NOW. some number of long ticks after midnight
		# well, who cares if it's time from Epoch or from last midnight?
		t0 = self._time - self._time % self.tickgap
		#it's position
		y0 = (self._nowrel + (t0 - self._time)/self.timerange*self._ltr)*height
		#distance between ticks
		dy = self._shortgap/self.timerange*height
		#how many ticks are below t0
		i = -(y0//dy)
		y0 += i*dy
		t0 += i*self._shortgap*self._ltr
		while y0 <= height:
			if i % self._ntick == 0:		#means long tick
				ctx.move_to(self.long_h[0], y0)
				ctx.line_to(self.long_h[1], y0)
				ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
				ctx.set_line_width(self.long_w)
				ctx.stroke()
				# Labels
				self._ticklabel.set_text(
					time.strftime(self.label_fmt, time.localtime(t0)))
				fontw, fonth = self._ticklabel.get_pixel_size()
				ctx.set_source_rgb(*self.style_color(gtk.STATE_INSENSITIVE))
				ctx.move_to(self.label_x - fontw/2,
							y0 - 0.5*fonth + self.label_y)
				ctx.show_layout(self._ticklabel)
			else:
				ctx.move_to(self.short_h[0], y0)
				ctx.line_to(self.short_h[1], y0)
				ctx.set_source_rgb(*self.style_color(gtk.STATE_NORMAL))
				ctx.set_line_width(self.short_w)
				ctx.stroke()
			i += 1
			t0 += self._shortgap*self._ltr
			y0 += dy

		#markers
		ctx.set_line_width(self.marker_w)
		ctx.set_source_rgb(*self.style_color(gtk.STATE_SELECTED))
		for m in self.markers:
			ym = (self._nowrel + (m - self._time)/self.timerange*self._ltr)*height
			if ym > 0 and ym < height:
				ctx.move_to(self.marker_h[0], ym)
				ctx.line_to(self.marker_h[1], ym)
		ctx.stroke()

	def do_size_request(self, req):
		"""size-request signal handler"""
		fw, fh = self._ticklabel.get_pixel_size()
		h_min, h_max = self._request_min_max(self.label_x, fw)
		req.height = 2*self.style.ythickness + fh*self.timerange/self.tickgap
		req.width  = 2*self.style.xthickness + h_max - h_min

	def _length(self):
		return self.get_allocation().height - 2*self.style.ythickness
	def _norm_pos(self, pos):
		return pos[1] - self.style.ythickness

def _test():
	STYLE = """
pixmap_path "."
style "wtf" {
fg[NORMAL] = "#02158F"		#0
fg[ACTIVE] = "#91BEF2"		#1
fg[PRELIGHT] = "#4E8EDA"	#2
fg[SELECTED] = "white"		#3
fg[INSENSITIVE] = "green"	#4
bg[NORMAL] = "#150926"
xthickness = 5
ythickness = 5
font_name = "12"
}
widget "*lineclock-widget" style "wtf" 
"""
	gtk.rc_parse_string(STYLE)
	window = gtk.Window()
	timeline = HLineClockWidget()
	timeline.markers = [time.time() + 30]
	timeline.timerange = 60
	timeline.tickgap = 10
	timeline.ntick = 5
	timeline.nowrel = 0.2
	timeline.label_fmt = "%M:%S"
	timeline.now_h = (-25, 0)
	timeline.ltr = 1
	window.add(timeline)
	window.connect("destroy", gtk.main_quit)
	gobject.timeout_add(1000, timeline.update)
	window.show_all()
	gtk.main()

if __name__ == "__main__" : _test()
