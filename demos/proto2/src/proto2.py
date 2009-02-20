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
from direct.gui.OnscreenText import OnscreenText
from direct.directtools.DirectGeometry import LineNodePath
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import *
from direct.task.Task import Task

from mdlib.panda.entity import *
from mdlib.panda.core import AbstractScene
from mdlib.panda.data import GOM
from mdlib.panda.physics import POM
from mdlib.panda.utils import *
from mdlib.types import Types

import sys, math

#base.wireframeOn()

class Camera(object):
    ZOOM = 30
    TARGET_DISTANCE = 4
    
    def __init__(self):
        base.disableMouse()
        base.camera.setPos(0,0,0)
        
    def followTarget(self, target):
        self.target = target
        self.update()
    
    def getPos(self):
        return base.camera.getPos()
    
    def zoomOut(self):
        base.camera.setY(base.camera, - self.ZOOM)

    def zoomIn(self):
        base.camera.setY(base.camera,  self.ZOOM)
        
    def update(self):
        base.camera.setPos(self.target.nodepath.getPos() - \
                           self.target.forward * self.TARGET_DISTANCE)
        base.camera.setZ(self.target.nodepath.getZ() + 1)
        base.camera.lookAt(self.target.nodepath.getPos())
        base.camera.setZ(self.target.nodepath.getZ() + 2)
        
        
class World(AbstractScene):
    def __init__(self):
        super(World, self).__init__()
        self.lines = render.attachNewNode("lines")
        
        #loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)
        
        self.mainLoop = taskMgr.add(self.updateTask, "update")
        self.mainLoop.last = 0
        
        self.track = GOM.createEntity(new_track_params)
        self.addEntity(self.track)
        #utils.showTrimeshLines(self.track.physics.geom, render, thickness=1)
        #self.track.nodepath.setColor(VBase4(0,0,0,0))
        self.track.nodepath.setCollideMask(BitMask32(1))
        
        self.ball = GOM.createEntity(ball_params)
        self.ball.nodepath.showTightBounds()
        collSphere = self.ball.nodepath.find("**/ball")
        collSphere.node().setIntoCollideMask(BitMask32(2))
        collSphere.node().setFromCollideMask(BitMask32.allOff())
        self.addEntity(self.ball)
        
        self.player = GOM.createEntity(player_params)
        self.player.nodepath.setPos(self.ball.nodepath.getPos())
        self.player.nodepath.setQuat(self.track.nodepath,Quat(1,0,0,0))
        self.player.forward = Vec3(0,1,0)
        self.addEntity(self.player)
        
        self.cam = Camera()
        self.cam.followTarget(self.player)
        self.camGroundZ = -999
        
        self.setSceneGraphNode(render)
        self._setupControls()
        self._setupCollisionDetection()
        self._setupLights()
        
        #self.ball.nodepath.setSa(0.7)
        #self.ball.nodepath.setTransparency(TransparencyAttrib.MAlpha)
        self.lastTile = ""
        
        
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    def updateTask(self, task):
        dt = task.time - task.last
        task.last = task.time
        if dt > .2: return Task.cont
        
        # keep the collision node perpendicular to the track, this is necessary
        # since the ball rolls all the time 
        self.ballCollNodeNp.setQuat(self.track.nodepath,Quat(1,0,0,0))
        
        if self.keyMap["right"] == True:
            right = self._rootNode.getRelativeVector(self.player.nodepath, 
                                                     Vec3(1,0,0))
            if self.ball.speed > 0:
                self.ball.turnRight()
            
        if self.keyMap["left"] == True:
            if self.ball.speed > 0:
                self.ball.turnLeft()
        
         # accelerate
        if self.keyMap["forward"] == True:
            if self.ball.speed < self.ball.MAX_SPEED:
                self.ball.speed += .2
            else:
                self.ball.speed = self.ball.MAX_SPEED
        else:
            if self.ball.speed > 0:
                self.ball.speed -= .1
        
        # brake
        if self.keyMap["backward"] == True:
            if self.ball.speed > 0:
                self.ball.speed -= .5
            
        if self.ball.speed < 0:
            self.ball.speed = 0
            
        # check track collisions
        # TODO must optimise this, no need to check the whole track,
        # but only the current segment
        self.picker.traverse(self.track.nodepath)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            
            firstGroundContact = -999
            firstTile = None
            for i in range(self.pq.getNumEntries()):
                entry = self.pq.getEntry(i)
                z = entry.getSurfacePoint(render).getZ()
                # check camera collision. There can be more than one
                if entry.getFromNodePath() == self.cameraCollNodeNp:
                    if z > firstGroundContact:
                        firstGroundContact = z
                        firstTile = entry.getIntoNodePath()
                # check ball's ray collision with ground
                elif entry.getFromNodePath() == self.ballCollNodeNp:
                    self.ballRayGroundZ = z
                    if entry != self.lastTile:
                        self.lastTile = entry
                        
            self.camGroundZ = firstGroundContact
        
        if self.camGroundZ == -999:
            # TODO
            print "Camera is not colliding with ground!"
                       
        # check for rays colliding with the ball
        self.picker.traverse(self.ball.nodepath)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            if self.pq.getNumEntries() == 1:
                entry = self.pq.getEntry(0)
                if entry.getFromNodePath() == self.cameraCollNodeNp:
                    self.camBallZ = entry.getSurfacePoint(render).getZ()
            else:
                raise AssertionError("must always be 1")
            
        if self.camGroundZ > self.camBallZ:
            # ground collision happened before ball collision, this means
            # that the ball is descending a slope
            # Get the row colliding with the cam's ray, get two rows after, 
            # set all of them transparent
            # TODO store the rows in a list, as I have to set the transparency
            # back to 0 after the ball has passed 
            row = firstTile.getParent()
            row.setSa(0.8)
            row.setTransparency(TransparencyAttrib.MAlpha)
                
        # forward vector of the ball expressed in the world coordinate space 
        forward = self._rootNode.getRelativeVector(self.player.nodepath,
                                                   Vec3(0,1,0)) 
        forward.setZ(0)
        forward.normalize()
        self.player.forward = forward
        speedVec = forward * dt * self.ball.speed
        self.player.nodepath.setPos(self.player.nodepath.getPos() + speedVec)
        
        # adjust height to be aligned with track
        #self.player.nodepath.setZ(0.13+self.ballCollNodeNp.getZ())
        previousZ = self.player.nodepath.getZ()
        newZ = 0.13+self.ballRayGroundZ
        self.player.nodepath.setZ(newZ)
        
        # rotate the ball
        self.ball.nodepath.setP(self.ball.nodepath.getP() -1 * dt * \
                                  self.ball.speed * self.ball.spinningFactor)
        self.ball.nodepath.setPos(self.player.nodepath.getPos())
        self.player.nodepath.setH(self.ball.nodepath.getH())
        
        self.update()
        self.cam.update()
        
        self.lines.removeNode()
        self.lines = render.attachNewNode("lines")
        
        self.render()
        
        return task.cont
    
    
    def _debugPosition(self):
        for text in aspect2d.findAllMatches("**/text").asList():
            text.getParent().removeNode()
        OnscreenText(text="Camera's Ray-Ball: %s" % self.camBallZ,
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.45), scale = .07)
        OnscreenText(text="Camera's Ray-Ground : %s" % self.camGroundZ,
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.55), scale = .07)
        OnscreenText(text="Camera: %s" % base.camera.getZ(),
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.65), scale = .07)
        OnscreenText(text="Ball ray-plane: %s" % self.ballRayGroundZ,
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.75), scale = .07)
        OnscreenText(text="Ball Z: %s" % self.ball.nodepath.getZ(),
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.85), scale = .07)
        OnscreenText(text="Player Z: %s" % self.player.nodepath.getZ(),
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.95), scale = .07)
        
    def _setupControls(self):
        self.keyMap = {"left":0, "right":0, "forward":0, "backward":0}
        base.accept("arrow_left", self.setKey, ["left",True])
        base.accept("arrow_right", self.setKey, ["right",True])
        base.accept("arrow_up", self.setKey, ["forward",True])
        base.accept("arrow_left-up", self.setKey, ["left",False])
        base.accept("arrow_right-up", self.setKey, ["right",False])
        base.accept("arrow_up-up", self.setKey, ["forward",False])
        base.accept("arrow_down", self.setKey, ["backward",True])
        base.accept("arrow_down-up", self.setKey, ["backward",False])
        base.accept("escape", sys.exit)
        
        base.accept("c", self._switchCamera)
        base.accept("p", self._debugPosition)
    
    def _switchCamera(self):
        base.oobe()
    
    def _setupLights(self):
        lAttrib = LightAttrib.makeAllOff()
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(.55, .55, .55, 1) )
        lAttrib = lAttrib.addLight( ambientLight )
        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setDirection( Vec3( 0, 0, -1 ) )
        directionalLight.setColor( Vec4( 0.375, 0.375, 0.375, 1 ) )
        directionalLight.setSpecularColor(Vec4(1,1,1,1))
        lAttrib = lAttrib.addLight( directionalLight )
      
    def _setupCollisionDetection(self):
        self.pq = CollisionHandlerQueue();
        
        self.ballRay = CollisionRay()
        self.ballRay.setOrigin(0,0,10)
        self.ballRay.setDirection(0,0,-1)
        self.ballCollNode = CollisionNode("ballRay")
        self.ballCollNodeNp = self.ball.nodepath.attachNewNode(self.ballCollNode)
        self.ballCollNodeNp.setQuat(self.track.nodepath,Quat(1,0,0,0))
        self.ballCollNode.setIntoCollideMask(BitMask32.allOff())
        self.ballCollNode.setFromCollideMask(BitMask32(1))
        self.ballCollNode.addSolid(self.ballRay)
        self.ballCollNodeNp.show()
  
        self.cameraRay = CollisionRay()
        # this must be relative to the camera, as just after I will attach the
        # collision node to the camera itself
        self.cameraRay.setOrigin(Point3(0,0,0)) 
        self.cameraRay.setDirection(0,1,0)
        self.cameraCollNode = CollisionNode("cameraRay")
        self.cameraCollNodeNp = base.camera.attachNewNode(self.cameraCollNode)
        # set the rotation a bit higher in order for the ray to pierce the ball
        # instead of aiming at his feet
        self.cameraCollNodeNp.setQuat(base.camera.getQuat() + Quat(.1,0,0,0))
        self.cameraCollNode.setIntoCollideMask(BitMask32.allOff())
        bm = BitMask32(1) # first bit on
        bm.setBit(1) # second bit on !!!!
        self.cameraCollNode.setFromCollideMask(bm)
        self.cameraCollNode.addSolid(self.cameraRay)
        self.cameraCollNodeNp.show()
        
        
        self.picker = CollisionTraverser()
        self.picker.addCollider(self.ballCollNodeNp, self.pq)
        self.picker.addCollider(self.cameraCollNodeNp, self.pq)
        
    def start(self):
        run()
    
if __name__ == '__main__':
    World().start()
    