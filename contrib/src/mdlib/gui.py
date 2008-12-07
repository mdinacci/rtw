# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module contains some utilities related to GUI development,
especially with PyGTK and Glade
"""

import gtk

class DoubleBufferedDrawingArea(gtk.DrawingArea):
    pass

class GladeView(object):
    """
    Make easier dealing with Glade and PyGTK. 
    Extend your GUI from this class.
    """
    def __init__(self, gladefile, main_window="MainWindow", is_gnome_app=False):
        """
        Check if the application is a GnomeApp and initialise the GUI
        """
        
        super(GladeView, self).__init__()
        
        if is_gnome_app:
            import gnome.ui
            gnome.init(gladefile[0:gladefile.index(".")], "999")

        self.wTree = gtk.glade.XML(gladefile)
        self.window = self.wTree.get_widget(main_window)
        if (self.window):
            dic = self._generate_callback_dictionary(gladefile)
            self.wTree.signal_autoconnect(dic)
            self.window.connect("destroy", gtk.main_quit)
            self.window.show_all()
    
    def _generate_callback_dictionary(self, gladefile):
        # TODO add automatic generation of callbacks
         
        callbacks = {}
        cb_names = glade_callbacks(gladefile)
        for cb_name in cb_names:
            callbacks[cb_name] = eval("self.%s" % cb_name)
        return callbacks
    
    def __getattr__(self,attr):
        """
        Redefine __getattr__ in order to access the widgets as if they were
        attribute of the class instance without having to call: 
        widget_tree.get_widget(widget_name)
        """
        
        value = ""
        try:
            value = self.__dict__[attr]
        except KeyError, err:
            value = self.wTree.get_widget(attr)
        
        return value

def glade_callbacks(glade_file):
    """ 
    Given a glade file, search the widget elements that have a signal child
    and returns a list of the existing callbacks.
    """
    
    from xml.etree.ElementTree import parse
    
    WIDGET_TAG = "widget"
    CHILD_TAG = "child"
    SIGNAL_TAG = "signal"
    HANDLER_TAG = "handler"
    
    callbacks = []

    def get_callbacks(element):
        for child in element.getchildren():
            if child.tag == SIGNAL_TAG:
                callback = child.get(HANDLER_TAG)
                callbacks.append(callback)
            elif child.tag == CHILD_TAG:
                widgets = child.findall(WIDGET_TAG)
                for widget in widgets:
                    get_callbacks(widget)
    
    tree = parse(glade_file)
    widgets = tree.findall(WIDGET_TAG)
    for widget in widgets:
        get_callbacks(widget)
        
    return callbacks
