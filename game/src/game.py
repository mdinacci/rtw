# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("game", INFO)

# configuration
from mdlib.panda import config as cfg
cfg.loadFile("../res/config.prc")
cfg.loadFile("../res/conf/options.prc")
cfg.loadFile("../res/conf/high.prc")

from mdlib.native import SystemManager
from mdlib.panda import eventCallback
from mdlib.panda.data import GOM
from mdlib.panda.input import InputManager

from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart
from pandac.PandaModules import WindowProperties, VirtualFileSystem, Filename
from pandac.PandaModules import ClockObject
from pandac.PandaModules import BitMask32, AntialiasAttrib, Quat, Vec3
from pandac.PandaModules import CollisionHandlerQueue, CollisionTraverser

from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
      
from gui import ScreenManager
from view import GameView
from entity import *
from state import GS, GameState

import event

import sys, time


class Game(object):
    
    DUMMY_VALUE = -999
    
    def __init__(self, view):
        self._view = view
        
        self._subscribeToEvents()
        self._setupInput()
        
        self._camGroundZ = self.DUMMY_VALUE
        self._lastTile = ""
        self._tileType = "neutral"
        self._lastTileType = "neutral"
        
        self._controlInverted = False
        
    def start(self):
        self._setupCollisionDetection()
        
        # HACK necessary to get the track's copy in the scenegraph
        self._track.reparentTo(self._view.scene._rootNode)
        
        self._view.scene.addEntity(self._track)
        self._view.scene.addEntity(self._ball)
        self._view.scene.addEntity(self._player)
        self._view.cam.followTarget(self._ball)
        self._view.showCursor(False)
        
        self._view.show()
        
        self._view.hud.timer.start()
        
        
    def setTrack(self, tid):
        # TODO remove first existing track from scene
        logger.info("Using track %s" % tid)
        
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/tracks/%s.track"% tid) ,".", 
                  VirtualFileSystem.MFReadOnly)
        
        self._track = GOM.getEntity(new_track_params)
        self._track.unfold()
        
        # TODO this should be done in data
        self._track.nodepath.setCollideMask(BitMask32(1))
        
        
    def setBall(self, ballName):
        # TODO remove first existing ball and player from scene
        logger.info("Using ball %s" % ballName)
        
        params = ballsMap[ballName]
        self._ball = GOM.getEntity(params)
        self._ball.nodepath.setPos(Point3(params["position"]["x"],
                                          params["position"]["y"],
                                          params["position"]["z"]))
        collSphere = self._ball.nodepath.find("**/ball")
        collSphere.node().setIntoCollideMask(BitMask32(2))
        collSphere.node().setFromCollideMask(BitMask32.allOff())
        self._player = GOM.getEntity(player_params)
        self._player.nodepath.setPos(self._ball.nodepath.getPos())
        self._player.nodepath.setQuat(self._track.nodepath,Quat(1,0,0,0))
        self._ball.forward = Vec3(0,1,0)
        
    
    def update(self, task):
        # steer
        
        if self._keyMap["right"] == True:
            if self._ball.physics.speed > 0:
                if self._controlInverted:
                    self._ball.turnLeft()
                else:
                    self._ball.turnRight()
            
        if self._keyMap["left"] == True:
            if self._ball.physics.speed > 0:
                if self._controlInverted:
                    self._ball.turnRight()
                else:
                    self._ball.turnLeft()
        
        if self._keyMap["forward"] == True:
            if self._controlInverted:
                self._ball.brake()
            else:
                self._ball.accelerate()
        else:
            self._ball.decelerate()
        
        if self._keyMap["backward"] == True:
            if self._controlInverted:
                self._ball.accelerate()
            else:
                self._ball.brake()
        
        if self._keyMap["jump"] == True:
            self._ball.jump()
            self._keyMap["jump"] = False
        
        # special actions
        
        if self._tileType == "neutral":
            self._ball.neutral()
        elif self._tileType == "jump":
            if self._lastTileType != "jump":
                self._ball.jump()
        elif self._tileType == "accelerate":
            self._ball.sprint()
        elif self._tileType == "slow":
            self._ball.slowDown()
        elif self._tileType == "freeze":
            if self._lastTileType != "freeze":
                self._ball.freeze()
        else:
            print "unknown type: " , self._tileType
        
        self._lastTileType = self._tileType
        
        # special items
        
        if self._ball.hasSpecialItem():
            item = self._ball.specialItem
            if item == "M":
                self._ball.minimize()
            elif item == "I":
                self._ball.invisibleMode()
            elif item == "+":
                self._view.hud.timer.addTime(30)
                self._view.hud.timer.flash()
            elif item == "-":
                self._view.hud.timer.removeTime(30)
                self._view.hud.timer.flash()
            elif item == "?":
                delay = Wait(3)
                f = Func(self.__setattr__,"controlInverted", True)
                f1 = Func(self.__setattr__,"controlInverted", False)
                Sequence(f, delay, f1).start()
                
            self._ball.specialItem = None
        
        if self._ball.physics.speed < 0:
            self._ball.physics.speed = 0
            
        return task.cont
    
    def simulationStep(self, task):
        self._view.cam.update()
        
        return task.cont
    
    def collisionStep(self, task):
        dt = globalClock.getDt()
        
        self._camGroundZ = self.DUMMY_VALUE
        ballIsCollidingWithGround = False
        
        # keep the collision node perpendicular to the track, this is necessary
        # since the ball rolls all the time 
        self._ballCollNodeNp.setQuat(self._track.nodepath,Quat(1,0,0,0))
        
        # check track collisions
        # TODO must optimise this, no need to check the whole track,
        # but only the current segment
        self._picker.traverse(self._track.nodepath)
        if self._collQueue.getNumEntries() > 0:
            self._collQueue.sortEntries()
            
            firstGroundContact = self.DUMMY_VALUE
            firstTile = None
            for i in range(self._collQueue.getNumEntries()):
                entry = self._collQueue.getEntry(i)
                z = entry.getSurfacePoint(render).getZ()
                # check camera collision. There can be more than one
                if entry.getFromNodePath() == self._cameraCollNodeNp:
                    if z > firstGroundContact:
                        firstGroundContact = z
                        firstTile = entry.getIntoNodePath()
                # check _ball's ray collision with ground
                elif entry.getFromNodePath() == self._ballCollNodeNp:
                    np = entry.getIntoNodePath()
                    rootNode = np.getParent().getParent().getParent()
                    if rootNode.hasTag("effect"):
                        self._ball.setSpecialItem(rootNode.getTag("effect"))
                        rootNode.removeNode()
                    else:    
                        # tell the _track which segment the _ball is on
                        self._track.setCurrentTile(np)
                        
                        # find out the tile type from the texture
                        textures = np.findAllTextures()
                        if textures.getNumTextures() > 1:
                            self._tileType = textures.getTexture(1).getName()
                        else:
                            self._tileType = textures.getTexture(0).getName()
                        #self._tileType = np.findAllTextures().getTexture(0).getName()
                    
                    self._ball.rayGroundZ = z
                    
                    ballIsCollidingWithGround = True
                    if entry != self._lastTile:
                        self._lastTile = entry
                        
            self._camGroundZ = firstGroundContact
        
        if ballIsCollidingWithGround == False:
            if self._ball.isJumping():
                print "no _ball-ground contact but jumping"
            else:
                print "no _ball-ground contact, losing"
                self._ball.getLost()
                self._view.gameIsAlive = False
                
                return task.done # automatically stop the task
        
        # check for rays colliding with the _ball
        self._picker.traverse(self._ball.nodepath)
        if self._collQueue.getNumEntries() > 0:
            self._collQueue.sortEntries()
            if self._collQueue.getNumEntries() == 1:
                entry = self._collQueue.getEntry(0)
                if entry.getFromNodePath() == self._cameraCollNodeNp:
                    self.camBallZ = entry.getSurfacePoint(render).getZ()
            else:
                raise AssertionError("must always be 1")
            
        #if self._camGroundZ > self.camBallZ:
                # ground collision happened before _ball collision, this means
                # that the _ball is descending a slope
                # Get the row colliding with the cam's ray, get two rows after, 
                # set all of them transparent
                # TODO store the rows in a list, as I have to set the transparency
                # back to 0 after the _ball has passed 
                #pass
                #row = firstTile.getParent()
                #row.setSa(0.8)
                #row.setTransparency(TransparencyAttrib.MAlpha)
        
        # HACK
        forward = self._view.scene._rootNode.getRelativeVector(
                                                   self._player.nodepath,
                                                   Vec3(0,1,0)) 
        forward.setZ(0)
        forward.normalize()
        speedVec = forward * dt * self._ball.physics.speed
        self._ball.forward = forward
        self._ball.physics.speedVec = speedVec

        self._player.nodepath.setPos(self._player.nodepath.getPos() + speedVec)
        self._player.nodepath.setZ(self._ball.rayGroundZ + 
                                  self._ball.jumpZ + \
                                  self._ball.physics.radius)
        
        # rotate the _ball
        self._ball.nodepath.setP(self._ball.nodepath.getP() -1 * dt * \
                                  self._ball.physics.speed * 
                                  self._ball.physics.spinningFactor)
        # set the _ball to the position of the controller node
        self._ball.nodepath.setPos(self._player.nodepath.getPos())
        # rotate the controller to follow the direction of the _ball
        self._player.nodepath.setH(self._ball.nodepath.getH())
        
        return task.cont
    
    def _setKey(self, key, value):
        self._keyMap[key] = value
        
    def _setupInput(self):
        self._keyMap = {"left":False, "right":False, "forward":False, \
                       "backward":False, "jump": False}
        
        self.inputMgr = InputManager()
        self.inputMgr.createSchemeAndSwitch("game")
        
        self.inputMgr.bindCallback(cfg.strValueForKey("options_steer_left"), 
                                   self._setKey, ["left",True], scheme="game")
        self.inputMgr.bindCallback(cfg.strValueForKey("options_steer_right"), 
                                   self._setKey, ["right",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_accelerate")
                                   , self._setKey, ["forward",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_brake"), 
                                   self._setKey, ["backward",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_jump"), 
                                   self._setKey, ["jump",True])
        
        key = cfg.strValueForKey("options_steer_left") + "-up"
        self.inputMgr.bindCallback(key, self._setKey, ["left",False])
        key = cfg.strValueForKey("options_steer_right") + "-up"
        self.inputMgr.bindCallback(key, self._setKey, ["right",False])
        key = cfg.strValueForKey("options_accelerate") + "-up"
        self.inputMgr.bindCallback(key, self._setKey, ["forward",False])
        key = cfg.strValueForKey("options_brake") + "-up"
        self.inputMgr.bindCallback(key, self._setKey, ["backward",False])
        
    def _setupCollisionDetection(self):    
        self._collQueue = CollisionHandlerQueue();
        
        # ball-ground collision setup
        self._ballCollNodeNp = self._ball.nodepath.attachCollisionRay(
                                              "ball-ground",
                                              0,0,10, # origin
                                              0,0,-1, # direction
                                              BitMask32(1),BitMask32.allOff())
        self._ballCollNodeNp.setQuat(self._track.nodepath, Quat(1,0,0,0))
        self._ballCollNodeNp.show()
        
        # camera-ball collision setup
        bmFrom = BitMask32(1); bmFrom.setBit(1)
        self._cameraCollNodeNp = self._view.cam.attachCollisionRay("camera-ball",
                                               0,0,0,
                                               0,1,0,
                                               bmFrom,BitMask32.allOff())
        self._cameraCollNodeNp.setQuat(self._view.cam.getQuat() + Quat(.1,0,0,0))
        self._cameraCollNodeNp.show()
        
        self._picker = CollisionTraverser()
        self._picker.setRespectPrevTransform(True)
        self._picker.addCollider(self._ballCollNodeNp, self._collQueue)
        self._picker.addCollider(self._cameraCollNodeNp, self._collQueue)
        
    def _subscribeToEvents(self):
        self._listener = DirectObject()
        self._listener.accept(event.BALL_SELECTED, self.setBall)
        self._listener.accept(event.TRACK_SELECTED, self.setTrack)
        

class GameApplication(object):

    dta = 0
    stepSize = 1/60.0

    def __init__(self):
        super(GameApplication, self).__init__()
        
        self._listener = DirectObject()
        
        if self._checkRequirements():
            
            self._subscribeToEvents()
            self._createWindow()
            
            GS.state.request(GameState.INITIALISE)
            
        else:
            self._quitInDespair("Requirements not satisfied", -2)
    
    
    def run(self):
        if cfg.boolValueForKey("cap-framerate"):
            FPS = 60
            globalClock = ClockObject.getGlobalClock()
            globalClock.setMode(ClockObject.MLimited)
            globalClock.setFrameRate(FPS)
        
        base.openDefaultWindow(startDirect=False, props=self._wp)
        
        self._screenMgr = ScreenManager()
        self._screenMgr.displayScreen("main")
        
        self._createGameAndView()
        
        taskMgr.run()
    
    @eventCallback
    def shutdown(self):
        sys.exit(0)
    
    @eventCallback
    def startGame(self):
        logger.info("Starting game")
        
        self._screenMgr.destroyCurrent()
        
        GS.state.request(GameState.PLAY)
        
        self._game.start()
        
        self._startProcesses()
    
    @eventCallback
    def exitGameRequest(self):    
        self._screenMgr.displayScreen("exit")
   
    def _createGameAndView(self):
        view = GameView()
        view.hide()
        self._game = Game(view)
   
    def _startProcesses(self):
        taskMgr.add(self._game.inputMgr.update, "update-input")
        taskMgr.add(self._game.collisionStep, "collision-step")
        taskMgr.add(self._game.simulationStep, "world-simulation")
        taskMgr.add(self._game.update, "update-objects")
        
    def _quitInDespair(msg, status):
        print msg
        sys.exit(status)
   
    def _subscribeToEvents(self):
        self._listener.accept(event.GAME_EXIT_REQUEST, self.exitGameRequest)
        self._listener.accept(event.GAME_DESTROY, self.shutdown)
        self._listener.accept(event.GAME_START, self.startGame)
    
    def _createWindow(self):
        self._wp = WindowProperties().getDefault()
        self._wp.setOrigin(0,0)
        self._wp.setFullscreen(cfg.boolValueForKey("options_fullscreen"))
        if not self._wp.getFullscreen():
            w,h = cfg.strValueForKey("options_resolution").split("x")
            self._wp.setSize(int(w),int(h))
    
    
    def _loadResources(self):
        vfs = VirtualFileSystem.getGlobalPtr()
        return vfs.mount(Filename("../res/scene.mf"),".",
                     VirtualFileSystem.MFReadOnly)
            
        
    def _checkRequirements(self):
        logger.debug("Checking system requirements")
        sm = SystemManager()

        dsNeeded = cfg.intValueForKey("required-space")
        enoughDS = sm.checkDiskSpace(sm.getSystemDrive(), dsNeeded)
        enoughRam = sm.checkRam(cfg.intValueForKey("required-ram"))
        
        return enoughRam and enoughDS 
        


if __name__ == '__main__':
    GameApplication().run()
    
    