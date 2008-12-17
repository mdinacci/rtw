# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

This module contains a collection of different cameras
"""

import direct.directbase.DirectStart
from pandac.PandaModules import Vec3, NodePath


class CameraManager(object):
    
    def __init__(self, inputSystem):
        self.ins = inputSystem
        self.cams = {"free": FreeCamera(self.ins), "fixed": None}
        self.active = self.cams["free"]
    
    def setActive(self, cameraName):
        if cameraName in self.cams.keys():
            self.active = self.cams[cameraName]
            self.active.reset()

class AbstractCamera(object):
    def reset(self):
        """ Abstract method to override """
        raise NotImplementedError()

class FixedCamera(AbstractCamera):
    def __init__(self, pos):
        base.disableMouse()
    
    def reset(self):
        pass
        
class FreeCamera(AbstractCamera):
    FORWARD = Vec3(0,2,0)
    BACK = Vec3(0,-1,0)
    LEFT = Vec3(-1,0,0)
    RIGHT = Vec3(1,0,0)
    UP = Vec3(0,0,1)
    DOWN = Vec3(0,0,-1)
    STOP = Vec3(0)
    walk = STOP
    strafe = STOP
    
    def __init__(self, ins):
        self.createVirtualNode()
        self.attachControls(ins)
        self.setupCamera()
        
        self.linearSpeed = 70
        taskMgr.add(self.mouseUpdate, 'mouse-task')
        taskMgr.add(self.moveUpdate, 'move-task')

    def reset(self):
        pass

    # FIXME InputSystem must be responsible for this !
    def attachControls(self, ins):
        ins.bind( "s" , self.__setattr__,["walk",self.STOP] )
        ins.bind( "w" , self.__setattr__,["walk",self.FORWARD])
        ins.bind( "s" , self.__setattr__,["walk",self.BACK] )
        ins.bind( "s-up" , self.__setattr__,["walk",self.STOP] )
        ins.bind( "w-up" , self.__setattr__,["walk",self.STOP] )
        ins.bind( "a" , self.__setattr__,["strafe",self.LEFT])
        ins.bind( "d" , self.__setattr__,["strafe",self.RIGHT] )
        ins.bind( "a-up" , self.__setattr__,["strafe",self.STOP] )
        ins.bind( "d-up" , self.__setattr__,["strafe",self.STOP] )
        ins.bind( "q" , self.__setattr__,["strafe",self.UP] )
        ins.bind( "q-up" , self.__setattr__,["strafe",self.STOP] )
        ins.bind( "e" , self.__setattr__,["strafe",self.DOWN] )
        ins.bind( "e-up" , self.__setattr__,["strafe",self.STOP] )
        
    def createVirtualNode(self):
        self.node = NodePath("vcam")
        self.node.reparentTo(render)
        self.node.setPos(0,0,2)
        self.node.setScale(0.05)
        self.node.showBounds()

    def setupCamera(self):
        base.disableMouse()
        camera.setPos( 0, -40, 20)
        camera.lookAt(0,0,0)
        camera.reparentTo(self.node)
        pl =  base.cam.node().getLens()
        pl.setFov(70)
        base.cam.node().setLens(pl)
    
    def mouseUpdate(self,task):
        """ this task updates the mouse """
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
            self.node.setH(self.node.getH() -  (x - base.win.getXSize()/2)*0.3)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2)*0.3)
        return task.cont

    def moveUpdate(self,task):
        """ this task makes the vcam move """
        # move where the keys set it
        self.node.setPos(self.node,self.walk*globalClock.getDt()*self.linearSpeed)
        self.node.setPos(self.node,self.strafe*globalClock.getDt()*self.linearSpeed)
        return task.cont
    