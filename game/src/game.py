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
from mdlib.panda.input import InputManager, SafeDirectObject
from mdlib.patterns import singleton

from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart
from pandac.PandaModules import WindowProperties, VirtualFileSystem, Filename
from pandac.PandaModules import ClockObject, RigidBodyCombiner, NodePath
from pandac.PandaModules import BitMask32, AntialiasAttrib, Quat, Vec3, Point3
from pandac.PandaModules import CollisionHandlerQueue, CollisionTraverser, \
CollisionHandlerEvent, CollisionNode, CollisionSphere

from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
from direct.showbase.PythonUtil import Functor
      
from gui import ScreenManager
from view import GameView
from data import TrackResult, GameMode
from state import GS, GameState
import utils

import pprofile as profile
import event, entity

import sys, time


class CheckpointDelegate(object):
    latestCp = None
    startPos = None
    
    
class Game(object):
    
    DUMMY_VALUE = -999
    
    def __init__(self, view):
        self._view = view
        
        self._setupInput()
        self._subscribeToEvents()
        
        self._cpDelegate = CheckpointDelegate()
        
        self._camGroundZ = self.DUMMY_VALUE
        self._lastTile = ""
        self._tileType = "neutral"
        self._lastTileType = "neutral"
        self._currentSegment = None
        
        self._track = None
        self._ball = None
        
        self._controlInverted = False
        
        self._gameIsAlive = True
    
    def start(self):
        self._loadTrack(GS.selectedTrack)
        self._loadBall(GS.selectedBall)
        
        self._setupCollisionDetection()
        
        self._view.scene.addEntity(self._track)
        self._view.scene.addEntity(self._ball)
        self._view.scene.addEntity(self._player)
        self._view.cam.followTarget(self._player)
        self._view.showCursor(False)
        
        self._view.show()
        
        self._view.hud.timer.resetAndStart()
        
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
        t = self._tileType
        if t == "neutral" or t == "N":
            self._ball.neutral()
        elif t == "jump" or t == "J":
            self._ball.jump()
        elif t == "accelerate" or t == "A":
            self._ball.sprint()
        elif t == "slow" or t == "S":
            self._ball.slowDown()
        elif t == "freeze" or t == "F":
            if not self._lastTileType == "F" and not self._lastTileType == "freeze":
                self._ball.freeze()
        else:
            print "unknown type: " , self._tileType
            self._ball.neutral()
        
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
                delay = Wait(1)
                f = Func(self.__setattr__,"_controlInverted", True)
                f1 = Func(self.__setattr__,"_controlInverted", False)
                Sequence(f, delay, f1).start()
                
            self._ball.specialItem = None
        
        if self._ball.physics.speed < 0:
            self._ball.physics.speed = 0
        
        self._tileType = "neutral"
        
        return task.cont
    
    def simulationStep(self, task):
        self._view.cam.update()
        
        return task.cont
    
    def collisionStep(self, task):
        if not self._gameIsAlive:
            print "no coll step "
            return task.cont
        
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
        #self._picker.traverse(self._currentSegment)

        if self._collQueue.getNumEntries() > 0:
            self._collQueue.sortEntries()
            
            for i in range(self._collQueue.getNumEntries()):
                entry = self._collQueue.getEntry(i)
                z = entry.getSurfacePoint(render).getZ()
                
                # check _ball's ray collision with ground
                if entry.getFromNodePath() == self._ballCollNodeNp:
                    np = entry.getIntoNodePath()
                    if np.getName() == "cp":
                        pass
                    
                    self._ball.rayGroundZ = z
                    
                    ballIsCollidingWithGround = True
                    if entry != self._lastTile:
                        self._lastTile = entry
                        
        if ballIsCollidingWithGround == False:
            if not self._ball.isJumping():
                print "no ball-ground contact, losing"
                
                self._playBallFallingSequence()
                
                return task.cont
                #return task.done # automatically stop the task
        
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
        self._player.nodepath.setZ(self._ball.rayGroundZ + self._ball.jumpZ + \
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
    
    @eventCallback
    def endTrack(self):
        self._ball.slowDown()
        self._view.hud.timer.stop() 
        trackTime = self._view.hud.timer.time
        
        info = GS.getTrackInfo(GS.selectedTrack)
        
        result = TrackResult()
        result.bestTime = utils.strTimeToTenths(trackTime)
        result.bid = GS.selectedBall
        result.tid = info.tid
        
        result.trophy = None
        if result.bestTime <= info.bronze:
            result.trophy = entity.bronze_cup_params
        if result.bestTime <= info.silver:
            result.trophy = entity.silver_cup_params
        if result.bestTime <= info.gold:
            result.trophy = entity.gold_cup_params
            
        GS.lastTrackResult = result
        GS.profile.update(result, GS.mode)
        
    @eventCallback
    def _onBallIntoCheckpoint(self, entry):
        logger.info("Checkpoint crossed")
        
        cp = entry.getIntoNodePath()
        self._cpDelegate.latestCp = cp
        
    @eventCallback
    def _onBallIntoSpecialTile(self, tile ,entry):
        logger.info("Ball on special tile")
        self._tileType = tile
        
    @eventCallback
    def _onBallIntoSpecialItem(self, item ,entry):
        logger.info("Ball on special item")
        self._ball.setSpecialitem(item)
        # TODO remove also node, get it from entry
    
    def _onBallIntoSegment(self, entry):
        logger.info("Rolling on segment")
        self._currentSegment.setCollideMask(BitMask32.allOff())
        self._currentSegment = entry.getIntoNodePath()
        self._currentSegment.setCollideMask(BitMask32(1))
    
    def _playBallFallingSequence(self):
        # play falling sequence and restart from latest 
        # checkpoint (or start point)
        sp = self._cpDelegate.startPos
        startPos = Point3(sp[0], sp[1], sp[2])
        if self._cpDelegate.latestCp is not None:
            startPos = self._cpDelegate.latestCp.getPos()
                
        seq = Sequence(Func(self.__setattr__,"_gameIsAlive",False), 
                       Func(self._ball.getLost, startPos),
                       Func(self.__setattr__,"_gameIsAlive",True),
                       Func(self._player.nodepath.setPos, 
                        self._ball.nodepath.getPos()))
        seq.start()
    
    def _loadTrack(self, tid):
        # TODO remove first existing track from scene
        
        logger.info("Using track %s" % tid)
        
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/tracks/%s.track"% tid) ,".", 
                  VirtualFileSystem.MFReadOnly)
        
        if self._track is not None:
            self._track.nodepath.removeNode()
        self._track = GOM.getEntity(entity.new_track_params, False)
        
        # TODO this should be done in data
        #self._track.nodepath.getChild(0).getChild(0).setCollideMask(BitMask32(1))
        
        self._currentSegment = self._track.nodepath.find("**/=start-point")
        self._currentSegment.setCollideMask(BitMask32(1))
        
        #self._track.nodepath.ls()
        
        """
        rbc = RigidBodyCombiner("rbc")
        rbcnp = NodePath(rbc)
        rbcnp.reparentTo(render)
        self._track.nodepath.reparentTo(rbcnp)
        rbc.collect()
        """

    def _loadBall(self, ballName):
        # TODO remove first existing ball and player from scene
        
        logger.info("Using ball %s" % ballName)
        
        if self._ball is not None:
            self._ball.nodepath.removeNode()
        
        params = entity.ballsMap[ballName]
        self._ball = GOM.getEntity(params, False)
        
        # place the ball at the beginning of the track
        t = self._track.nodepath.find("**/=start-point")

        pos = map(lambda x: float(x), t.getTag("start-point").split(","))
        # HACK 5 is half segment, unless the segment is a curve :/
        self._ball.nodepath.setPos(render,pos[0], pos[1]-5, pos[2])
        
        self._cpDelegate.startPos = pos
        
        self._player = GOM.getEntity(entity.player_params)
        self._player.nodepath.setPos(self._ball.nodepath.getPos())
        self._player.nodepath.setQuat(self._track.nodepath,Quat(1,0,0,0))
        self._ball.forward = Vec3(0,1,0)
        
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
        self.inputMgr.bindCallback("p", base.oobe)
        
        self.inputMgr.bindCallback("escape", GS.state.request, [GameState.PAUSE])
        
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
        # orient it perpendicular to the track
        self._ballCollNodeNp.setQuat(self._track.nodepath, Quat(1,0,0,0))
        self._ballCollNodeNp.show()
        
        self._picker = CollisionTraverser()
        self._picker.addCollider(self._ballCollNodeNp, self._collQueue)
        #self._picker.setRespectPrevTransform(True)
        
        self._collHandler = CollisionHandlerEvent()
        self._collHandler.addInPattern(event.BALL_INTO)
        
        collNode = self._ball.nodepath.find("**/ball")
        self._picker.addCollider(collNode, self._collHandler)
    
    def _subscribeToEvents(self):
        do = DirectObject()
        do.accept("ball-into-segment", self._onBallIntoSegment)
        do.accept(event.BALL_INTO_CHECKPOINT, self._onBallIntoCheckpoint)
        do.accept(event.BALL_INTO_SLOW, self._onBallIntoSpecialTile, ["slow"])
        do.accept(event.BALL_INTO_ACCELERATE, self._onBallIntoSpecialTile, 
                  ["accelerate"])
        do.accept(event.BALL_INTO_JUMP, self._onBallIntoSpecialTile, ["jump"])
        
        self._listener = do
        

class GameApplication(object):

    dta = 0
    stepSize = 1/60.0

    def __init__(self):
        singleton(self)
        super(GameApplication, self).__init__()
        
        GS.setApplication(self)
        
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
        
        taskMgr.run()
    
    @eventCallback
    def shutdown(self):
        sys.exit(0)
    
    @eventCallback
    def startRace(self):
        logger.info("Starting game")
        self._screenMgr.destroyCurrent()
        
        GS.state.request(GameState.PLAY)
    
    @eventCallback
    def exitGameRequest(self):    
        self._screenMgr.displayScreen("exit")
    
    @eventCallback
    def endRace(self):
        GS.state.request(GameState.NEXT_TRACK)
        
    def startProcesses(self):
        taskMgr.add(self._game.inputMgr.update, "update-input")
        taskMgr.add(self._game.collisionStep, "collision-step")
        taskMgr.add(self._game.update, "update-objects")
        # nothing to do for now
        #taskMgr.add(self._game.simulationStep, "world-simulation")
        
    def stopProcesses(self):
        taskMgr.remove("update-input")
        taskMgr.remove("collision-step")
        taskMgr.remove("world-simulation")
        taskMgr.remove("update-objects")
    
    def createGameAndView(self):
        # TODO first destroy (or reset) previous game and view if they exists
        self._view = GameView()
        self._view.hide()
        self._game = Game(self._view)
   
    def _quitInDespair(msg, status):
        print msg
        sys.exit(status)
   
    def _subscribeToEvents(self):
        self._listener.accept(event.GAME_EXIT_REQUEST, self.exitGameRequest)
        self._listener.accept(event.GAME_DESTROY, self.shutdown)
        self._listener.accept(event.GAME_START, self.startRace)
        self._listener.accept(event.RESTART_TRACK, self.startRace)
        self._listener.accept(event.END_TRACK, self.endRace)
        self._listener.accept(event.UNPAUSE_GAME, GS.state.request, 
                              [GameState.NEUTRAL])
        self._listener.accept("l", self.__wireframe)
        
    a = 0
    def __wireframe(self):
        if self.a ==0:
            base.wireframeOn()
            self.a == 1 
            self._game._track.nodepath.hide()
        else:
            base.wireframeOff()
            self.a == 0
            self._game._track.nodepath.show()
    
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
        
    game = property(fget = lambda self: self._game)
    view = property(fget = lambda self: self._view)
    screen = property(fget = lambda self: self._screenMgr)


if __name__ == '__main__':
    GameApplication().run()
    
    