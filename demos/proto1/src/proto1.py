# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import *
loadPrcFile("../res/Config.prc")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *

from mdlib.panda.entity import *
from mdlib.panda.core import AbstractScene
from mdlib.panda.data import GOM

import sys

base.wireframeOn()

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
        
        base.accept("escape", sys.exit)
        base.accept("i", self.moveBall, [0,0.5,0])
        base.accept("j", self.moveBall, [-0.5,0,0])
        base.accept("k", self.moveBall, [0,-0.5,0])
        base.accept("l", self.moveBall, [0.5,0,0])
        
        taskMgr.add(self.updateTask, "update")
        
        self.cam = Camera()
        
        self.track = GOM.createEntity(new_track_params)
        self.addEntity(self.track)
        
        self.player = GOM.createEntity(player_params)
        self.addEntity(self.player)
        
        ball_params["render"]["parentNode"] = self.player.UID
        ball_params["position"]["x"] = self.player.position.x
        ball_params["position"]["y"] = self.player.position.y
        ball_params["position"]["z"] = self.player.position.z
        self.ball = GOM.createEntity(ball_params)
        self.addEntity(self.ball)
        
        self._setupCollisionDetection()
        
        self.actor = ActorNode("playeractor")
        self.actorNp = render.attachNewNode(self.actor)

        base.physicsMgr.attachPhysicalNode(self.actor)
        self.player.nodepath.reparentTo(self.actorNp)
        self.ball.nodepath.reparentTo(self.actorNp)
        
        self.setSceneGraphNode(render)
        
    def moveBall(self, x,y,z):
        #self.player.nodepath.setPos(self.player.nodepath, x,y,z)
        
        self.actor.getPhysical(0).addLinearForce(LinearVectorForce(0,4000,0))
        print self.player.position, self.player.render.nodepath.getPos()
        print self.actor.getPhysical(0)
        print self.ball.position, self.ball.render.nodepath.getPos()
        print self.ballCollNodeNp.getPos()
        print self.actorNp.getPos()

    def updateTask(self, task):
        #self.update()
        # check ball-plane collision
        self.picker.traverse(self.track.nodepath)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            for i in range(self.pq.getNumEntries()):
                pass#print self.pq.getEntry(i).getIntoNodePath()
                
        return task.cont
       
    
    def _setupCollisionDetection(self):
        self.pq = CollisionHandlerQueue();
        
        self.ballRay = CollisionRay()
        self.ballRay.setOrigin(0,0,10)
        self.ballRay.setDirection(0,0,-1)
        self.ballCollNode = CollisionNode("ballRay")
        self.ballCollNodeNp = self.player.nodepath.attachNewNode(self.ballCollNode)
        self.ballCollNodeNp.setPos(self.player.nodepath.getPos())
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
    