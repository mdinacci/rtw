# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

Hello world with Panda3D
"""

import gtk
try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)
    
import gobject
import time

from pandac.PandaModules import loadPrcFileData 
loadPrcFileData("", "window-type none")
from pandac.PandaModules import WindowProperties 
import direct.directbase.DirectStart 

from direct.showbase.DirectObject import DirectObject 

class World(DirectObject):
    def __init__(self, parentWindow):
        wp = WindowProperties.getDefault()
        wp.setSize(400,300)
        wp.setParentWindow(parentWindow)
        base.openWindow(props=wp)
        
        environ = loader.loadModel("models/environment")
        environ.reparentTo(render)
        environ.setScale(0.25,0.25,0.25)
        environ.setPos(-8,42,0)
        
if __name__ == "__main__":
    panda_init = False

    def panda_idle():
        global panda_init
        if not panda_init:
            World(drawingArea.window.xid)
            panda_init = True
        
        taskMgr.step()
        time.sleep(0.001)
        return True

    def printHello(w):
        print "Button pressed"

    gobject.idle_add(panda_idle)
    
    wTree = gtk.glade.XML("gui.glade")
    window = wTree.get_widget("MainWindow")
    window.connect("destroy", gtk.main_quit)
    btn = wTree.get_widget("btn")
    btn.connect("clicked", printHello)
    drawingArea = wTree.get_widget("da")
    
    window.show_all()
    
    gtk.main()
