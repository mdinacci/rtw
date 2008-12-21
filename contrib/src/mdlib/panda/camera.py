# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

This module contains a collection of different cameras
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("camera", DEBUG)

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task

from pandac.PandaModules import Vec3, NodePath, PandaNode, WindowProperties, Camera

from mdlib.panda import pandaCallback
from mdlib.decorator import traceMethod

__all__  = ["RoamingCamera","FixedCamera", "TheBallCamera", "DebugCamera"]

class AbstractCamera(Camera):
    FORWARD = Vec3(0,2,0)
    BACK = Vec3(0,-1,0)
    LEFT = Vec3(-1,0,0)
    RIGHT = Vec3(1,0,0)
    UP = Vec3(0,0,1)
    DOWN = Vec3(0,0,-1)
    STOP = Vec3(0)
    
    moveTaskName = "move_task"
    
    
    def __init__(self, name):
        super(AbstractCamera, self).__init__(name)
        
        self.walk = self.STOP
        self.strafe = self.STOP
        self.linearSpeed = 40
        
        # cameras must be enabled by calling enable()
        self.isActive = False
        
        # accept input and configure controls
        self.ins = DirectObject()
        self._setupInput()
        
        # attach to the base.camera node
        base.camera.attachNewNode(self)
        
        # camera specific initialisation
        self._initialise()
    
    def _setupInput(self):
        raise NotImplementedError()
        
    def _initialise(self):
        """ 
        Initialise camera properties like position and hpr 
        This method is supposed to be called only once.
        To disable and enable the camera, use self.disable and self.enable
        """
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

    def disable(self):
        taskMgr.remove(self.moveTaskName)
        self.setActive(False)
      
      
    def enable(self):
        taskMgr.add(self.moveTask, self.moveTaskName)
        self.setActive(True)

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


class DebugCamera(AbstractCamera):
    def __init__(self):
        super(DebugCamera, self).__init__("debug")
    
    def _initialise(self):
        base.oobe()
        
    def _setupInput(self):
        pass

class WASDCamera(AbstractCamera):
    def __init__(self, name="wasd"):
        super(WASDCamera, self).__init__(name)
    
    def _setupInput(self):
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


class TheBallCamera(AbstractCamera):
    """ 
    This camera constantly target an actor from a certain distance,
    following its movements.
    """
    def __init__(self, target, minDistance = 5.0, maxDistance = 15.0, height= 5):
        super(TheBallCamera, self).__init__("third_person")
        self._target = target
        self._virtualTarget = NodePath(PandaNode("virtual_target"))
        # FIXME I don't like that is reparented to render
        self._virtualTarget.reparentTo(render)
        self._minDistance = minDistance
        self._maxDistance = maxDistance
        self._height = height
    
    def _setupInput(self):
        # this camera has no controls
        return None 
    
    def enable(self):
        super(TheBallCamera, self).enable()
        base.disableMouse()
        #self._updatePosition(None)
        np = self._target.getNodePath()
        taskMgr.add(self._updatePosition, 'updatePositionTask')
        
    def disable(self):
        super(TheBallCamera, self).disable()
        taskMgr.remove('updatePositionTask') 
    
    @pandaCallback
    def _updatePosition(self, task):
        target = self._target.getNodePath()
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
        
        return Task.cont 
    
    def _initialise(self):
        base.disableMouse()
        

class FixedCamera(WASDCamera):
    """
    This camera is suited to select objects in the scene.
    It can be moved using the "wasd" key's combination and doesn't 
    allow any rotation (yet...)
    
    TODO implement rotation
    """
    def __init__(self):
        super(FixedCamera, self).__init__("fixed")
    
    def enable(self):
        super(FixedCamera, self).enable()
        base.disableMouse()
        self.showCursor(True)
        
    def disable(self):
        super(FixedCamera, self).disable()
        self.showCursor(False)
    
    def _initialise(self):
        self.enable()
    
           
class RoamingCamera(WASDCamera):
    """
    FPS-like camera, moving the mouse around will update the position of the camera.
    """
    
    mouseTask= "mouse-task"
    
    
    def __init__(self):
        super(RoamingCamera, self).__init__("roam")
        self.linearSpeed = 20
        self.angularSpeed = 4
    
    def _initialise(self):
        base.disableMouse()
        pl = self.getLens()
        pl.setFov(70)
        self.setLens(pl)
        
    def lookAtOrigin(self):
        base.camera.lookAt(0,0,0)
        
    def disable(self):
        super(RoamingCamera, self).disable()
        taskMgr.remove('Roam_Camera')
    
    def enable(self):
        super(RoamingCamera, self).enable()
        base.disableMouse()
        self.showCursor(False)
        taskMgr.add(self.mouseUpdate, 'Roam_Camera')
    
    @pandaCallback
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
        else:
            logger.debug("Failed to move pointer at origins")
            base.camera.lookAt(0,0,0)
              
        return task.cont
