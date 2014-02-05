#!/usr/bin/env python
# -*- coding: utf-8-*-

"""
Filename: gui.py
Author: Marco Dinacci <marco.dinacci@gmail.com>
License:

"""

from mdlib.gui.gtk import GladeView
from mdlib.decorator import Property
from mdlib.patterns import SimpleObservable, Observer

import sys
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gtk.glade
except ImportError, error:
    sys.exit(1)

        
class Track(object, SimpleObservable):
    """ A track is a circuit where the ball rolls. """

    _coords = []
    
    def __init__(self):
        super(Track, self).__init__()
        SimpleObservable.__init__(self)
        
    def add_coord(self, coord):
        self._coords.append(coord)
        self.notify()

        if len(self._coords) > 1:
            prev_coord = self._coords[-2]
            print "\n=========================="
            print "New coord: ", coord
            print "Previous coord: " , prev_coord
            # angular_coeff of straight line
            denom = float(coord[0] - prev_coord[0])
            if denom != 0:
                m = (coord[1] - prev_coord[1]) / denom
                print "Angular coefficient reference line: ", m 
                
                intercept = coord[1] + (m * coord[0] * -1)
                print "Intercept reference line: ", intercept
                
                m_ortho = m * -1
                print "Angular coefficient orthogonal line: ", m_ortho
                
                intercept_ortho = coord[1] + (m_ortho * coord[0] * -1)
                print "Intercept orthogonal line: ", intercept_ortho
                
                m_parallel = m
                intercept_parallel = intercept - 40
                print "Intercept parallel: ", intercept_parallel
                
                x = - (intercept_ortho - intercept_parallel) / (m_ortho - m_parallel)
                y = intercept_ortho + (m_ortho * x)
            
                # calculate intersection between parallel line and perpendicular line to find out
                # the second point to draw
                """
                a_ortho = m_ortho * -1
                print "A ortho: ", a_ortho
                
                a_parallel = m_parallel * -1
                print "A parallel: ", a_parallel
                
                b_ortho = 1
                b_parallel = 1
                
                c_ortho = intercept_ortho
                print "C ortho: ", c_ortho
                c_parallel = intercept_parallel
                print "C parallel: ", c_parallel
                
                x = (c_ortho - c_parallel) / float(a_ortho - a_parallel)
                y = (c_ortho) / (a_ortho * x)
                """
                c = (x, y) 
                print "X,Y: ", c 
                self._coords.append(c)
                self.notify()
                print "==========================\n"
    
    # TODO coords must be a read-only property except for add_coord
    def get_xy_coords(self):
        return tuple(self._coords)
    
    def get_latest_coords(self, qty = 3):
        return self._coords[-qty:]
    
    def is_saved(self):
        pass
    
    def save(self):
        pass

class FreeHandController(object):
    def __init__(self, canvas):
        super(FreeHandController, self).__init__()
        self.canvas = canvas

    def _add_coord(self, coord):
        track.add_coord(coord)

    def start_drawing(self, event):
        track.is_drawing = True
        self._add_coord(event.get_coords())
        
    def keep_drawing(self, event):
        self._add_coord(event.get_coords())
    
    def stop_drawing(self, event):
        track.is_drawing = False
    
    def get_points(self):
        return track.get_xy_coords()
    
    def get_latest_points(self, qty):
        return track.get_latest_coords(qty)
    
class FreeHandCanvas(gtk.DrawingArea, Observer):
    """ This is the canvas where the track is sketched """
    
    _pixmap = None # backing pixmap where the drawing is performed
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        Observer.__init__(self)
        
        self.set_sensitive(True)
        self.set_double_buffered(False) # redundant because of _pixmap
        self.add_events(gtk.gdk.BUTTON_RELEASE_MASK |
                                gtk.gdk.BUTTON1_MOTION_MASK |
                                gtk.gdk.POINTER_MOTION_HINT_MASK |
                                gtk.gdk.BUTTON_PRESS_MASK |
                                gtk.gdk.KEY_PRESS_MASK |
                                gtk.gdk.KEY_RELEASE_MASK
                                )

        self.connect("expose_event", self._on_expose)
        self.connect("configure_event", self._on_configure)
        self.connect('motion_notify_event', self._on_motion_notify)
        self.connect('button_release_event', self._on_button_release)
        self.connect('button_press_event', self._on_button_press)
        self.connect('key_press_event', self._on_key_press)

        self.controller = FreeHandController(self)
        
        # register with track in order to get notified in case of modifications
        track.register(self)
    
    def update(self):
        """ 
        Track has changed, update the drawing. 
        Supports only adding new points, one at a time  
        """
        point = self.controller.get_latest_points(1)[0]
        self.draw_brush(point[0], point[1])
        
    def draw_brush(self, x, y, w = 6, h = 6):
        """ Draw a rectangle on the canvas """
        rect = (int(x-w/2), int(y-h/2), w, h)
        self._pixmap.draw_rectangle(self.get_style().black_gc, True,
                              rect[0], rect[1], rect[2], rect[3])
        self.queue_draw_area(rect[0], rect[1], rect[2], rect[3])

    def _on_configure(self, widget, event):
        """ GTK callback """
        x, y, width, height = widget.get_allocation()
        self._pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self._pixmap.draw_rectangle(widget.get_style().white_gc,
                          True, 0, 0, width, height)
        # TODO draw grid
        
        cell_size = 10
        lines_gc = self._pixmap.new_gc()
        main_lines_gc = self._pixmap.new_gc()    
        lines_gc.set_foreground(self._pixmap.get_colormap().alloc_color(50000,50000,50000))
        main_lines_gc.set_foreground(self._pixmap.get_colormap().alloc_color(65535,0,0))

        # draw columns
        for i in range(0,int(width/cell_size)+1):
            gc = None
            if i % 5 == 0:
                gc = main_lines_gc
            else:
                gc = lines_gc
                
            self._pixmap.draw_lines(gc,
                                    [(i*cell_size,0), (i*cell_size,height)])
        
        # draw lines
        for i in range(0, int(height/cell_size)+1):
            gc = None 
            if i % 5 == 0:
                gc = main_lines_gc
            else:
                gc = lines_gc
                
            self._pixmap.draw_lines(gc,
                                    [(0,i*cell_size), (width,i*cell_size)])
        
        return True
    
    def _on_expose(self, widget, event):
        """ GTK callback """
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self._pixmap, x, y, x, y, width, height)
        if self._pixmap != None:
            pass # FIXME redraw track !

        return False

    def _on_key_press(self, widget, event):
        print dir(event)

    def _on_motion_notify(self, widget, event):
        """ GTK callback """
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
    
        if state & gtk.gdk.BUTTON1_MASK and self._pixmap != None:
            self.controller.keep_drawing(event)

        return True

    def _on_button_press(self, widget, event):
        """ GTK callback """
        if event.button == 1 and self._pixmap != None:
            self.controller.start_drawing(event)
        return True

    def _on_button_release(self, widget, event):
        """ GTK callback """
        if event.button == 1 and self._pixmap != None:
            self.controller.stop_drawing(event)
        return True

class EditorView(GladeView):
    def __init__(self, gladefile, main_window="MainWindow", is_gnome_app=False):
        super(EditorView,self).__init__(gladefile, main_window, is_gnome_app)
        self._init_freehand_view()
        self.presenter = EditorPresenter(self)
    
    def _init_freehand_view(self):
        canvas = FreeHandCanvas()
        self.freehand_viewport.add(canvas)
        canvas.show()

    def on_newLevelButton_clicked(self,widget):
        self.presenter.create_new_level()
    
    def on_openLevelButton_clicked(self,widget):
        print "open Level"
    
    def on_saveLevelButton_clicked(self,widget):
        print "save Level"
    
    def on_generateLevelButton_clicked(self,widget):
        print "generate Level"

class EditorModel(object):
    _level = None
    
    def __init__(self):
        super(EditorModel, self).__init__()
    
    @Property
    def level():
        doc = """level attribute property."""

        def fget(self):
            return self._level

        def fset(self, value):
            self._level = value

        def fdel(self):
            del self._level

        return locals()

class EditorPresenter(object):
    def __init__(self, view):
        super(EditorPresenter, self).__init__()

        self.view = view
        self.model = EditorModel()
    
    def create_new_level(self):
        if self.model.level != None:
            # TODO user is editing a level, save it first
            if not self.model.level.is_saved():
                self.view.save_canvas()
            
            self.model.level.save()
            self.model.level = None
            self.create_new_level()
        else:
            self.model.level = Track()
            # Normally the view should observe the model and update itself
            self.view.init_canvas()
            
    def set_level_filename(self, filename):
        # exception to the MVP rule, the view has to pass a variable
        # as it's stored in a save dialog which is closed before 
        # calling this method
        self.model.level.filename = filename

if __name__ == '__main__':
    import sys
    sys.path.append("resources")
    
    track = Track()
    view = EditorView("gui2.glade", "MainWindow", True)
    
    gtk.main()

