# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import *
loadPrcFile("../res/Config.prc")
#loadPrcFileData("", "want-directtools 1")
#loadPrcFileData("", "want-tk 1")

import direct.directbase.DirectStart
from direct.directtools.DirectGeometry import LineNodePath
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *
from direct.task.Task import Task

from mdlib.panda.entity import *
from mdlib.panda.core import AbstractScene
from mdlib.panda.data import GOM
from mdlib.panda.physics import POM

import sys

#base.wireframeOn()

class Camera(object):
    FORWARD = Vec3(0,2,0)
    BACK = Vec3(0,-1,0)
    LEFT = Vec3(-1,0,0)
    RIGHT = Vec3(1,0,0)
    UP = Vec3(0,0,1)
    DOWN = Vec3(0,0,-1)
    STOP = Vec3(0)
    walk = STOP
    strafe = STOP
    ZOOM_SPEED = 30
    
    def __init__(self):
        self.createVirtualNode()
        self.setupCamera()
        self.attachControls()
        
        self.linearSpeed = 80
        taskMgr.add(self.mouseUpdate, 'mouse-task')
        taskMgr.add(self.moveUpdate, 'move-task')
        
    def attachControls(self):
        base.accept( "s" , self.__setattr__,["walk",self.STOP] )
        base.accept( "w" , self.__setattr__,["walk",self.FORWARD])
        base.accept( "s" , self.__setattr__,["walk",self.BACK] )
        base.accept( "s-up" , self.__setattr__,["walk",self.STOP] )
        base.accept( "w-up" , self.__setattr__,["walk",self.STOP] )
        base.accept( "a" , self.__setattr__,["strafe",self.LEFT])
        base.accept( "d" , self.__setattr__,["strafe",self.RIGHT] )
        base.accept( "a-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "d-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "q" , self.__setattr__,["strafe",self.UP] )
        base.accept( "q-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "e" , self.__setattr__,["strafe",self.DOWN] )
        base.accept( "e-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept('page_up', self.zoomIn)
        base.accept('page_down', self.zoomOut)
        base.accept('wheel_up-up', self.zoomIn)
        base.accept('wheel_down-up', self.zoomOut)
        base.accept('0', lambda: base.camera.lookAt(0,0,0))
    
    def zoomOut(self):
        base.camera.setY(base.camera, - self.ZOOM_SPEED)

    def zoomIn(self):
        base.camera.setY(base.camera,  self.ZOOM_SPEED)
        
    def createVirtualNode(self):
        self.node = NodePath("vcam")
        self.node.reparentTo(render)
        self.node.setPos(0,0,2)
        self.node.setScale(0.05)
        self.node.showBounds()

    def setupCamera(self):
        base.disableMouse()
        camera.setPos( 0, -15, 10.5)
        camera.lookAt(0,0,0)
        camera.reparentTo(self.node)
    
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
    

class World(AbstractScene):
    def __init__(self):
        super(World, self).__init__()
        self.lines = render.attachNewNode("lines")
        
        loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)
        
        base.accept("escape", sys.exit)
        base.accept("i", self.moveBall, [0,0.5,0])
        base.accept("j", self.moveBall, [-0.5,0,0])
        base.accept("k", self.moveBall, [0,-0.5,0])
        base.accept("l", self.moveBall, [0.5,0,0])
        base.accept("u", self.moveBall, [0,0,0.5])
        base.accept("o", self.moveBall, [0,0,-0.5])
        base.accept("i-up", self.stopBall)
        base.accept("j-up", self.stopBall)
        base.accept("k-up", self.stopBall)
        base.accept("l-up", self.stopBall)
        base.accept("u-up", self.moveBall, [0,0,0])
        base.accept("o-up", self.moveBall, [0,0,0])
        
        self.mainLoop = taskMgr.add(self.updateTask, "update")
        self.mainLoop.last = 0
        
        self.cam = Camera()
        
        self.track = GOM.createEntity(new_track_params)
        self.addEntity(self.track)
        
        self.displayTrack(self.track.physics.geom)
            
        self.player = GOM.createEntity(player_params)
        self.player.nodepath.showTightBounds()
        self.addEntity(self.player)
        
        ball_params["render"]["parentNode"] = self.player.UID
        
        self.ball = GOM.createEntity(ball_params)
        self.addEntity(self.ball)
        
        self.setSceneGraphNode(render)
        self._setupCollisionDetection()
        
        self.lastTile = ""
    
    
    def displayTrack(self, g):
        lines = LineNodePath(parent = render, thickness = 3.0, colorVec = Vec4(1, 1, 0, 1))
        lines.reset()
        for i in xrange(g.getNumTriangles()):
            a = Point3(0)
            b = Point3(0)
            c = Point3(0)
            g.getTriangle( i, a, b, c )
            l = (
                  (a.getX(), a.getY(), a.getZ()),\
                  (b.getX(), b.getY(), b.getZ()),\
                  (c.getX(), c.getY(), c.getZ()),\
                  (a.getX(), a.getY(), a.getZ())
                )
            lines.drawLines([l])
        
        lines.create()
            
            
    def displayLines(self, entity):
        p1 = Point3(0,0,0)
        p2 = Point3(0,0,0)
        entity.physics.geom.getAABB(p1,p2)
        lines = LineNodePath(parent = self.lines, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
        lines.reset()
        
        # lower rectangle
        l1 = (
              (p1.getX(), p1.getY(), p1.getZ()),
              (p2.getX(), p1.getY(), p1.getZ()),
              (p2.getX(), p2.getY(), p1.getZ()),
              (p1.getX(), p2.getY(), p1.getZ()),
              (p1.getX(), p1.getY(), p1.getZ()),
              )
        lines.drawLines([l1])
        
        # upper rectangle
        l2 = (
              (p1.getX(), p1.getY(), p2.getZ()),
              (p2.getX(), p1.getY(), p2.getZ()),
              (p2.getX(), p2.getY(), p2.getZ()),
              (p1.getX(), p2.getY(), p2.getZ()),
              (p1.getX(), p1.getY(), p2.getZ()),
              )
        lines.drawLines([l2])
        
        # junctions
        l3 = zip(l1,l2)
        lines.drawLines(l3)
        
        lines.create()


    
    def stopBall(self):
        self.player.physics.xForce = 0
        self.player.physics.xForce = 0
        self.player.physics.xForce = 0
        
        
    def moveBall(self, x,y,z):
        self.player.physics.xForce = x
        self.player.physics.yForce = y
        self.player.physics.zForce = z

    def updateTask(self, task):
        dt = task.time - task.last
        task.last = task.time
        if dt > .2: return Task.cont
        
        POM.update(self)
        # keep the rotation perpendicular to the track 
        self.ballCollNodeNp.setQuat(self.track.nodepath,Quat(1,0,0,0))
        
        # check ball-plane collision
        self.picker.traverse(self.track.nodepath)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            pickedObject = self.pq.getEntry(0)
            if pickedObject != self.lastTile:
                self.lastTile = pickedObject
                print "Colliding with: ", pickedObject.getIntoNodePath()
            
        self.update()
        
        self.lines.removeNode()
        self.lines = render.attachNewNode("lines")
        self.displayLines(self.player)
        self.displayLines(self.track)
        
        self.render()
        
        return task.cont
       
    
    def _setupCollisionDetection(self):
        self.pq = CollisionHandlerQueue();
        
        self.ballRay = CollisionRay()
        self.ballRay.setOrigin(0,0,10)
        self.ballRay.setDirection(0,0,-1)
        self.ballCollNode = CollisionNode("ballRay")
        self.ballCollNodeNp = self.player.nodepath.attachNewNode(self.ballCollNode)
        self.ballCollNodeNp.setQuat(self.track.nodepath,Quat(1,0,0,0))
        self.ballCollNode.setIntoCollideMask(BitMask32.allOff())
        self.ballCollNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.ballCollNode.addSolid(self.ballRay)
        self.ballCollNodeNp.show()
        
        self.picker = CollisionTraverser()
        self.picker.addCollider(self.ballCollNodeNp, self.pq)
        
    def start(self):
        run()
    
        
if __name__ == '__main__':
    World().start()
    