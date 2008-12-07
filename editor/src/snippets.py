class A():
    a = "1"
    b = "2"
    c = {"z":"1"}
    def __getattr__(self,attr):
        print "IN ATTR"
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self.c[attr] 
        
        
a = A()
print a.a,a.b,a.z

def save_canvas(self):
        from os import environ
        chooser = gtk.FileChooserDialog(title=None,
                                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
        buttons=(gtk.STOCK_CANCEL, 
                 gtk.RESPONSE_CANCEL, 
                 gtk.STOCK_SAVE,
                 gtk.RESPONSE_OK))
        chooser.set_current_folder("%s" % environ['HOME'])

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            if '.' in filename:
                filename = filename[:filename.index('.')] + ".track"
            else:
                filename = filename + ".track"

        chooser.destroy() 
        self.presenter.set_track_filename(filename)

class SlopeEditorController: pass

class SlopeEditorCanvas(gtk.DrawingArea):
    
    _pixmap = None # backing pixmap where the drawing is performed
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
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

        #self.controller = SlopeEditorController(self)
        
        
    def _on_configure(self, widget, event):
        """ GTK callback """
        x, y, width, height = widget.get_allocation()
        self._pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self._pixmap.draw_rectangle(widget.get_style().white_gc,
                          True, 0, 0, width, height)
        return True
    
    def _on_expose(self, widget, event):
        """ GTK callback """
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self._pixmap, x, y, x, y, width, height)
        if self._pixmap != None:
            pass # FIXME redraw track !

        return False


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
    
