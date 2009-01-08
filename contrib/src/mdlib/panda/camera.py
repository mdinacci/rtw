# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

TODO rename to scene.py

This module contains a collection of different cameras

TODO:
- add wheel mouse support for some cameras
- add a refresh rate for the mouse (1/30):
    curTime = globalClock.getFrameTime()
    if (curTime - MOUSE_REFRESH_RATE > self.lastTaskTime):
      self.lastTaskTime = curTime
      # cache the mouse position
      self.mousePosX, self.mousePosY = self._getCurrentMousePos()

      # if the mouse is fixed to the center of the window, reset the mousepos
      if self.mouseFixed and (self.mousePosX != 0.0 or self.mousePosY != 0.0):
        self.setMouseCentered()
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("camera", DEBUG)

import direct.directbase.DirectStart
from direct.task.Task import Task

from pandac.PandaModules import Vec3, NodePath, PandaNode, WindowProperties, Camera

from mdlib.panda import pandaCallback, SafeDirectObject
from mdlib.decorator import traceMethod

__all__  = ["RoamingCamera","FixedCamera", "TheBallCamera", "DebugCamera",
            "FORWARD","BACK","LEFT","RIGHT","UP","DOWN","STOP"]

FORWARD = Vec3(0,2,0)
BACK = Vec3(0,-1,0)
LEFT = Vec3(-1,0,0)
RIGHT = Vec3(1,0,0)
UP = Vec3(0,0,1)
DOWN = Vec3(0,0,-1)
STOP = Vec3(0)


class WASDCamera(Camera):
    """ A camera that supports navigation through WASD keys """
    def __init__(self, name, inputMgr):
        super(WASDCamera, self).__init__(name)
        
        self.walk = STOP
        self.strafe = STOP
        self.linearSpeed = 40
        self.angularSpeed = 4
        base.disableMouse()
        
        # cameras must be enabled by calling enable()
        self.isActive = False
        
        # attach to the base.camera node
        base.camera.attachNewNode(self)
        
        inputMgr.bindCallback( "w" , self.__setattr__,["walk",FORWARD], scheme="base")
        inputMgr.bindCallback( "s" , self.__setattr__,["walk",BACK], scheme="base")
        inputMgr.bindCallback( "a" , self.__setattr__,["strafe",LEFT], scheme="base")
        inputMgr.bindCallback( "d" , self.__setattr__,["strafe",RIGHT], scheme="base")
        inputMgr.bindCallback( "w-up" , self.__setattr__,["walk",STOP], scheme="base")
        inputMgr.bindCallback( "s-up" , self.__setattr__,["walk",STOP], scheme="base")
        inputMgr.bindCallback( "a-up" , self.__setattr__,["strafe",STOP], scheme="base")
        inputMgr.bindCallback( "d-up" , self.__setattr__,["strafe",STOP], scheme="base")
        inputMgr.bindCallback( "q" , self.__setattr__,["strafe",UP], scheme="base")
        inputMgr.bindCallback( "e" , self.__setattr__,["strafe",DOWN], scheme="base")
        inputMgr.bindCallback( "q-up" , self.__setattr__,["strafe",STOP], scheme="base")
        inputMgr.bindCallback( "e-up" , self.__setattr__,["strafe",STOP], scheme="base")
    
    def getPos(self):
        return base.camera.getPos()

    def setPos(self, x, y, z):
        base.camera.setPos(x, y, z)
        
    def lookAt(self, x, y, z):
        base.camera.lookAt(x, y, z)
    
    def lookAtOrigin(self):
        base.camera.lookAt(0,0,0)
        
    def showCursor(self, show = True):
        """ Hide the mouse cursor """
        props = WindowProperties()
        props.setCursorHidden(not show)
        base.win.requestProperties(props)
        
    def move(self):
        # move where the keys set it
        base.camera.setPos(base.camera,self.walk*globalClock.getDt()*self.linearSpeed)
        base.camera.setPos(base.camera,self.strafe*globalClock.getDt()*self.linearSpeed)
 
       
class FixedCamera(WASDCamera):
    """ A WASD camera that can't rotate using the mouse """
    def __init__(self, inputMgr):
        super(FixedCamera, self).__init__("fixed-camera", inputMgr)
        self.showCursor(True)
    
    def update(self): 
        self.move()
        

class RoamingCamera(WASDCamera):
    """ 
    A WASD camera that can also rotate using the mouse. 
    Very similar to a FPS camera
    """
    def __init__(self, inputMgr):
        print "CREATING ROAMING CAMERA"
        super(RoamingCamera, self).__init__("free-camera", inputMgr)
        pl = self.getLens()
        pl.setFov(70)
        self.setLens(pl)
        self.showCursor(False)
        
    def update(self):
        self.move()
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
            base.camera.setH(base.camera.getH() -  (x - base.win.getXSize()/2) * 
                             globalClock.getDt() * self.angularSpeed)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2) *
                             globalClock.getDt() * self.angularSpeed)
        else:
            base.camera.lookAt(0,0,0)


class DebugCamera(Camera):
    """
    This camera is used during debugging phases with directtools in order to
    do not influence or disturb the panda main's camera like the other
    camera will likely do. It does nothing but to abilitate the OOBE mode.
    """
    def __init__(self):
        super(DebugCamera, self).__init__("debug")
        base.disableMouse()
        base.oobe()


class TheBallCamera(WASDCamera):
    """ 
    This camera constantly target an actor from a certain distance,
    following its movements. It doesn't move around the X axis and
    keep a distance between minDistance and maxDistance in the yz space.
    
    FIXME it moves around the X axis 
    """
    def __init__(self, inputMgr, target=None, parent=None, minDistance = 5.0, 
                 maxDistance = 15.0, height= 5):
        super(TheBallCamera, self).__init__("ball-camera", inputMgr)
        self._target = target
        self._virtualTarget = NodePath(PandaNode("virtual_target"))
        if parent == None:
            parent = render
        self._virtualTarget.reparentTo(parent)
        self._minDistance = minDistance
        self._maxDistance = maxDistance
        self._height = height
        self.showCursor(False)
    
    def setTarget(self, target):
        self._target = target
    
    def enable(self):
        super(TheBallCamera, self).enable()
        base.disableMouse()
        
    def update(self):
        self.move()
        target = self._target
        camvec = target.getPos() - base.camera.getPos()
        #camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if(camdist > self._maxDistance):
            #base.camera.setPos(base.camera.getPos() + camvec*(camdist-self._maxDistance))
            prevX = base.camera.getX()
            pos = base.camera.getPos() + camvec*(camdist-self._maxDistance)
            pos.setX(prevX)
            pos.setZ(target.getZ() + self._height)
            base.camera.setPos(pos)
            camdist = self._maxDistance
        if(camdist < self._minDistance):
            #base.camera.setPos(base.camera.getPos() - camvec*(self._minDistance-camdist))
            prevX = base.camera.getX()
            pos = base.camera.getPos() - camvec*(self._minDistance-camdist)
            pos.setX(prevX)
            pos.setZ(target.getZ() + self._height)
            base.camera.setPos(pos)
            camdist = self._minDistance
        
        self._virtualTarget.setPos(target.getPos())
        self._virtualTarget.setZ(target.getZ() +2)#+ self._height/2)
        base.camera.lookAt(self._virtualTarget) 
    