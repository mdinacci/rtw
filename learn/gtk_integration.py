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
from pandac.PandaModules import Point3
import direct.directbase.DirectStart 

from direct.actor import Actor
from direct.interval.IntervalGlobal import *
from direct.task.Task import Task

from direct.showbase.DirectObject import DirectObject 

import math

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
        import sys
        self.accept("escape", sys.exit)
        
        taskMgr.add(self.SpinCameraTask, "SpinCameraTask")
        self.addPanda()
    
    
    def SpinCameraTask(self,task):
        angledegrees = task.time * 6.0
        angleradians = angledegrees * (math.pi / 180.0)
        base.camera.setPos(20*math.sin(angleradians),-20.0*math.cos(angleradians),3)
        base.camera.setHpr(angledegrees, 0, 0)
        return Task.cont

    def addPanda(self):
        self.pandaActor = Actor.Actor("models/panda-model",{"walk":"models/panda-walk4"})
        self.pandaActor.setScale(0.005,0.005,0.005)
        self.pandaActor.reparentTo(render)
        self.pandaActor.loop("walk")
        #Create the four lerp intervals needed to walk back and forth
        pandaPosInterval1= self.pandaActor.posInterval(13,Point3(0,-10,0), startPos=Point3(0,10,0))
        pandaPosInterval2= self.pandaActor.posInterval(13,Point3(0,10,0), startPos=Point3(0,-10,0))
        pandaHprInterval1= self.pandaActor.hprInterval(3,Point3(180,0,0), startHpr=Point3(0,0,0))
        pandaHprInterval2= self.pandaActor.hprInterval(3,Point3(0,0,0), startHpr=Point3(180,0,0))
        
        #Create and play the sequence that coordinates the intervals
        pandaPace = Sequence(pandaPosInterval1, pandaHprInterval1,
                             pandaPosInterval2, pandaHprInterval2, name = "pandaPace")
        pandaPace.loop()
        
    def destroy(self):
        self.ignoreAll() 

        
if __name__ == "__main__":
    panda_init = False

    def panda_idle():
        global panda_init
        if not panda_init:
            World(da.window.xid)
            panda_init = True
        
        taskMgr.step()
        time.sleep(0.001)
        return True

    def printHello(w,y):
        print "event: %s" % ( w)

    gobject.idle_add(panda_idle)

    class pd(gtk.DrawingArea):
        def __init__(self):
            gtk.DrawingArea.__init__(self)
            self.connect("expose_event", self.expose)
            self.connect("focus", self.printHello)
            self.set_sensitive(True)
            
        def printHello(self, event):
            print "yo: ", event
            
        def expose(self, widget, event):
            return False
        
        def is_focus(self):
            return True
        
        def is_focus(self, whatever):
            return True
    
    window = gtk.Window()
    window.connect("destroy", gtk.main_quit)
    da = pd()
    window.add(da)
    window.show_all()
    
    gtk.main()
