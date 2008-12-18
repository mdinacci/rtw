# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

This module contains a collection of different cameras
"""

__all__  = ["FreeCamera","FixedCamera"]

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import Vec3, NodePath, WindowProperties, Camera

class AbstractCamera(Camera):
    FORWARD = Vec3(0,2,0)
    BACK = Vec3(0,-1,0)
    LEFT = Vec3(-1,0,0)
    RIGHT = Vec3(1,0,0)
    UP = Vec3(0,0,1)
    DOWN = Vec3(0,0,-1)
    STOP = Vec3(0)
    
    def __init__(self, name):
        super(AbstractCamera, self).__init__(name)
        
        self.walk = self.STOP
        self.strafe = self.STOP
        self.linearSpeed = 50
        
        # accept input and configure controls
        self.ins = DirectObject()
        self._attachControls()
        
        # attach to the base.camera node
        base.camera.attachNewNode(self)
        
        # camera specific initialisation
        self.initialise()
        
        # animate the camera
        taskMgr.add(self.moveTask, 'move-task')
    
    def _attachControls(self):
        self.ins.accept( "s" , self.__setattr__,["walk",self.STOP] )
        self.ins.accept( "w" , self.__setattr__,["walk",self.FORWARD])
        self.ins.accept( "s" , self.__setattr__,["walk",self.BACK] )
        self.ins.accept( "s-up" , self.__setattr__,["walk",self.STOP] )
        self.ins.accept( "w-up" , self.__setattr__,["walk",self.STOP] )
        self.ins.accept( "a" , self.__setattr__,["strafe",self.LEFT])
        self.ins.accept( "d" , self.__setattr__,["strafe",self.RIGHT] )
        self.ins.accept( "a-up" , self.__setattr__,["strafe",self.STOP] )
        self.ins.accept( "d-up" , self.__setattr__,["strafe",self.STOP] )
        self.ins.accept( "q" , self.__setattr__,["strafe",self.UP] )
        self.ins.accept( "q-up" , self.__setattr__,["strafe",self.STOP] )
        self.ins.accept( "e" , self.__setattr__,["strafe",self.DOWN] )
        self.ins.accept( "e-up" , self.__setattr__,["strafe",self.STOP] )
        
    def initialise(self):
        """ Initialise camera properties like position and hpr """
        raise NotImplementedError()
        
    def getPos(self):
        return base.camera.getPos()

    def setPos(self, x, y, z):
        base.camera.setPos(x, y, z)
        
    def lookAt(self, x, y, z):
        base.camera.lookAt(x, y, z)

    def showCursor(self, show = True):
        """ Hide the mouse cursor """
        props = WindowProperties()
        props.setCursorHidden(not show)
        base.win.requestProperties(props)

    def destroy(self):
        """ 
        Very important, it detaches the camera completely from its parent nodepath
        and stop receving events 
        
        TODO check for correctness
        """
        self.setActive(False)
        self.ignoreAll() 
        base.camera.removeNode(self)

    def moveTask(self,task):
        """ this task makes the vcam move """
        # move where the keys set it
        base.camera.setPos(base.camera,self.walk*globalClock.getDt()*self.linearSpeed)
        base.camera.setPos(base.camera,self.strafe*globalClock.getDt()*self.linearSpeed)
        
        return task.cont

class FixedCamera(AbstractCamera):
    """
    This camera is suited to select objects in the scene.
    It can be moved using the "wasd" key's combination and doesn't 
    allow any rotation YET.
    
    TODO implement rotation
    """
    def __init__(self, pos):
        super(FixedCamera, self).__init__("fixed")
    
    def initialise(self):
        base.disableMouse()
        self.showCursor(True)
        self.setActive(True)
        
        
class FreeCamera(AbstractCamera):
    """
    FPS-like camera, moving the mouse around will update the position of the camera.
    """
    def __init__(self):
        super(FreeCamera, self).__init__("free")
        self.linearSpeed = 65
        self.angularSpeed = 5
        taskMgr.add(self.mouseUpdate, 'mouse-task')

    def initialise(self):
        base.disableMouse()
        #camera.setPos( 0, -40, 20)
        #camera.lookAt(0,0,0)
        pl = self.getLens()
        pl.setFov(70)
        self.setLens(pl)
        self.setActive(True)
        self.showCursor(False)
    
    def mouseUpdate(self,task):
        """ this task updates the mouse """
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
            base.camera.setH(base.camera.getH() -  (x - base.win.getXSize()/2) * 
                             globalClock.getDt() * self.angularSpeed)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2) *
                             globalClock.getDt() * self.angularSpeed)
            
        return task.cont
