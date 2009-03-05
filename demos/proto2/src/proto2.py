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
from mdlib.panda.core import AbstractScene, AbstractLogic, AbstractApplication
from mdlib.panda.data import GOM
from mdlib.panda.input import *
from mdlib.panda.utils import *
from mdlib.types import Types

import sys, math

#base.wireframeOn()

class Camera(object):
    ZOOM = 30
    TARGET_DISTANCE = 10
    
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

        z = self.target.jumpZ
        base.camera.setZ(self.target.nodepath.getZ() -z + 1)
        pos = self.target.nodepath.getPos()
        pos.setZ(pos.getZ() -z)
        base.camera.lookAt(pos)
        base.camera.setZ(self.target.nodepath.getZ() -z + 3)
    

HEIGHT_TRACK = 0.5

class GameLogic(AbstractLogic):
    DUMMY_VALUE = -999
    
    # the view is not really the view but just the scene for now.
    def __init__(self, view):
        super(GameLogic, self).__init__(view)
        
        self.env = GOM.createEntity(environment_params)
        self.view.addEntity(self.env)
        
        self.track = GOM.createEntity(new_track_params)
        self.track.nodepath.setCollideMask(BitMask32(1))
        self.view.addEntity(self.track)
        
        self.ball = GOM.createEntity(ball_params)
        self.ball.nodepath.showTightBounds()
        collSphere = self.ball.nodepath.find("**/ball")
        collSphere.node().setIntoCollideMask(BitMask32(2))
        collSphere.node().setFromCollideMask(BitMask32.allOff())
        self.view.addEntity(self.ball)
        
        self.player = GOM.createEntity(player_params)
        self.player.nodepath.setPos(self.ball.nodepath.getPos())
        self.player.nodepath.setQuat(self.track.nodepath,Quat(1,0,0,0))
        self.ball.forward = Vec3(0,1,0)
        self.view.addEntity(self.player)
        
        # normally the view should create it 
        self.cam = Camera()
        self.cam.followTarget(self.ball)
        self.camGroundZ = -999
        self.view.cam = self.cam
        
        # HACK
        self.view.player = self.player
        self.view.ball = self.ball
        self.view.track = self.track

        self.lastTile = ""
        self.tileType = "neutral"
        self.lastTileType = "neutral"
        
        self._setupCollisionDetection()

    
    def update(self, task):
        self.inputMgr.update()
        
        return task.cont
    
    
    def updatePhysics(self, task):
        dt = globalClock.getDt()
        if dt > .2: return task.cont
        
        self.camGroundZ = self.DUMMY_VALUE
        ballIsCollidingWithGround = False
        
        # keep the collision node perpendicular to the track, this is necessary
        # since the ball rolls all the time 
        self.ballCollNodeNp.setQuat(self.track.nodepath,Quat(1,0,0,0))
        
        # check track collisions
        # TODO must optimise this, no need to check the whole track,
        # but only the current segment
        self.picker.traverse(self.track.nodepath)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            
            firstGroundContact = self.DUMMY_VALUE
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
                    np = entry.getIntoNodePath()
                    #print np
                    self.tileType = np.findAllTextures().getTexture(0).getName()
                    self.ball.RayGroundZ = z
                    ballIsCollidingWithGround = True
                    if entry != self.lastTile:
                        self.lastTile = entry
                        
            self.camGroundZ = firstGroundContact
        
        if ballIsCollidingWithGround == False:
            if self.ball.isJumping():
                print "no ball-ground contact but jumping"
                pass
            else:
                print "no ball-ground contact, losing"
                self.ball.getLost()
                self.view.gameIsAlive = False
                return task.done # automatically stop the task
        
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
            
        #if self.camGroundZ > self.camBallZ:
                # ground collision happened before ball collision, this means
                # that the ball is descending a slope
                # Get the row colliding with the cam's ray, get two rows after, 
                # set all of them transparent
                # TODO store the rows in a list, as I have to set the transparency
                # back to 0 after the ball has passed 
                #pass
                #row = firstTile.getParent()
                #row.setSa(0.8)
                #row.setTransparency(TransparencyAttrib.MAlpha)
            
        forward = self.view._rootNode.getRelativeVector(self.player.nodepath,
                                                   Vec3(0,1,0)) 
        forward.setZ(0)
        forward.normalize()
        speedVec = forward * dt * self.ball.speed
        self.ball.forward = forward
        self.ball.speedVec = speedVec

        self.player.nodepath.setPos(self.player.nodepath.getPos() + speedVec)
        self.player.nodepath.setZ(self.ball.RayGroundZ + self.ball.jumpZ + \
                                  self.ball.physics.radius + HEIGHT_TRACK)
           
        # rotate the ball
        self.ball.nodepath.setP(self.ball.nodepath.getP() -1 * dt * \
                                  self.ball.speed * self.ball.spinningFactor)
        # set the ball to the position of the controller node
        self.ball.nodepath.setPos(self.player.nodepath.getPos())
        # rotate the controller to follow the direction of the ball
        self.player.nodepath.setH(self.ball.nodepath.getH())
            
        return task.cont
    
    
    def resetGame(self):
        self.player.nodepath.setPos(Point3(12,7,.13))
        self.ball.nodepath.setPos(Point3(12,7,.13))
        self.ball.nodepath.setQuat(Quat(1,0,0,0))
        self.view.gameIsAlive = True
    
    
    def updateLogic(self, task):
        # steer
        
        if self.keyMap["right"] == True:
            right = self.view._rootNode.getRelativeVector(self.player.nodepath, 
                                                     Vec3(1,0,0))
            if self.ball.speed > 0:
                self.ball.turnRight()
            
        if self.keyMap["left"] == True:
            if self.ball.speed > 0:
                self.ball.turnLeft()
        
        if self.keyMap["forward"] == True:
            self.ball.accelerate()
        else:
            self.ball.decelerate()
        
        if self.keyMap["backward"] == True:
            self.ball.brake()
        
        if self.keyMap["jump"] == True:
            self.ball.jump()
            self.keyMap["jump"] = False
        
        # special actions
        if self.tileType == "neutral":
            self.ball.neutral()
        elif self.tileType == "jump":
            if self.lastTileType != "jump":
                self.ball.jump()
        elif self.tileType == "accelerate":
            self.ball.sprint()
        elif self.tileType == "slow":
            self.ball.slowDown()
        
        self.lastTileType = self.tileType
        
        
        if self.ball.speed < 0:
            self.ball.speed = 0
            
        return task.cont
    
    
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    
    def debugPosition(self):
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
        OnscreenText(text="Ball ray-plane: %s" % self.ball.RayGroundZ,
                              style=1, fg=(1,1,1,1),
                              pos=(-0.9,-0.75), scale = .07)
        
        
    def _setupCollisionDetection(self):
        self.pq = CollisionHandlerQueue();
        
        # ball-ground collision setup
        self.ballCollNodeNp = self.ball.nodepath.attachCollisionRay("ball-ground",
                                              0,0,10, # origin
                                              0,0,-1, # direction
                                              BitMask32(1),BitMask32.allOff())
        self.ballCollNodeNp.setQuat(self.track.nodepath, Quat(1,0,0,0))
        self.ballCollNodeNp.show()
        
        # camera-ball collision setup
        bmFrom = BitMask32(1); bmFrom.setBit(1)
        self.cameraCollNodeNp = base.camera.attachCollisionRay("camera-ball",
                                               0,0,0,
                                               0,1,0,
                                               bmFrom,BitMask32.allOff())
        self.cameraCollNodeNp.setQuat(base.camera.getQuat() + Quat(.1,0,0,0))
        self.cameraCollNodeNp.show()
        
        self.picker = CollisionTraverser()
        self.picker.setRespectPrevTransform(True)
        self.picker.addCollider(self.ballCollNodeNp, self.pq)
        self.picker.addCollider(self.cameraCollNodeNp, self.pq)
        
       
    def _subscribeToEvents(self):
        self.keyMap = {"left":False, "right":False, "forward":False, \
                       "backward":False, "jump": False}
        
        self.inputMgr = InputManager(base)
        self.inputMgr.createSchemeAndSwitch("game")
        
        self.inputMgr.bindCallback("arrow_left", self.setKey, ["left",True], scheme="game")
        self.inputMgr.bindCallback("arrow_right", self.setKey, ["right",True])
        self.inputMgr.bindCallback("arrow_up", self.setKey, ["forward",True])
        self.inputMgr.bindCallback("arrow_left-up", self.setKey, ["left",False])
        self.inputMgr.bindCallback("arrow_right-up", self.setKey, ["right",False])
        self.inputMgr.bindCallback("arrow_up-up", self.setKey, ["forward",False])
        self.inputMgr.bindCallback("arrow_down", self.setKey, ["backward",True])
        self.inputMgr.bindCallback("arrow_down-up", self.setKey, ["backward",False])
        self.inputMgr.bindCallback("space", self.setKey, ["jump",True])
        
        self.inputMgr.bindCallback("c", self.view.switchCamera)
        self.inputMgr.bindCallback("d", self.debugPosition)
        
    
class World(AbstractScene):
    
    def __init__(self):
        super(World, self).__init__()
        self.lines = render.attachNewNode("lines")
        loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)
        
        self.setSceneGraphNode(render)
        #self._setupCollisionDetection()
        self._setupLights()
        self.gameIsAlive = True
        
    
    def update(self, task):
        #dt = globalClock.getDt()
        #if dt > .2: return task.cont
        
        if self.gameIsAlive:
        
            self.cam.update()
            
            self.lines.removeNode()
            self.lines = render.attachNewNode("lines")
            
        return task.cont
        
    
    def switchCamera(self):
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
      
        

class GameApplication(AbstractApplication):

    def _subscribeToEvents(self):
        base.accept("escape", self.shutdown)
        base.accept("r", self.restartGame)
    
    def _createLogicAndView(self):
        self.scene = World()
        self.logic = GameLogic(self.scene)
    
    def restartGame(self):
        taskMgr.remove("update-input")
        taskMgr.remove("update-logic")
        taskMgr.remove("update-physics")
        taskMgr.remove("update-scene")
        self.logic.resetGame()
        self.start()
    
    def start(self):
        taskMgr.add(self.logic.update, "update-input")
        taskMgr.add(self.logic.updateLogic, "update-logic")
        taskMgr.add(self.logic.updatePhysics, "update-physics")
        taskMgr.add(self.scene.update, "update-scene")
    
    def shutdown(self):
        sys.exit()
       
# set a fixed frame rate 
from pandac.PandaModules import ClockObject
FPS = 40
globalClock = ClockObject.getGlobalClock()
#globalClock.setMode(ClockObject.MLimited)
#globalClock.setFrameRate(FPS)

      
if __name__ == '__main__':
    GameApplication().start()
    run()
    