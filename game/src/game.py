# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("game", DEBUG)

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
from pandac.PandaModules import BitMask32, Quat, Vec3, Point3
from pandac.PandaModules import CollisionHandlerQueue, CollisionTraverser, \
CollisionHandlerEvent, CollisionNode, CollisionSphere, CollisionHandlerFloor

from direct.interval.MetaInterval import Sequence, Parallel
from direct.interval.FunctionInterval import Wait, Func
from direct.showbase.PythonUtil import Functor
      
from gui import ScreenManager
from view import GameView, SemaphoreTimer
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
    
    _collDelta = 0
    _simDelta = 0
    _collStep = 1/30.0
    _simStep = 1/60.0
    _updateDelta = 0
    _updateStep = 1/60.0
    
    def __init__(self, view):
        self._view = view

        self._cpDelegate = CheckpointDelegate()
        
        self._setupInput()
        self._subscribeToEvents()
        self._setupCollisionDetection()
        
        self._camGroundZ = self.DUMMY_VALUE
        self._lastTile = ""
        self._tileType = "neutral"
        self._lastTileType = "neutral"
        self._currentSegment = None
        
        self._track = None
        self._ball = None
        
        self._controlInverted = False
        self._gameIsAlive = False
        
        #base.wireframeOn()
        
    def prestart(self):
        logger.info("Prestarting game")
        self._loadTrack(GS.selectedTrack)
        self._loadBall(GS.selectedBall)
        
        self._view.scene.addEntity(self._track)
        self._view.scene.addEntity(self._ball)
        self._view.scene.addEntity(self._ballCtrl)
        self._view.cam.followTarget(self._ballCtrl)
    
        # start for a moment the game in order to correctly position the ball
        f1 = Func(self.__setattr__, "_gameIsAlive", True)
        f2 = Func(self.__setattr__, "_gameIsAlive", False)
        Sequence(f1, Wait(.1), f2).start()
        
        # display the view but hides the HUD in order to show the countdown
        # timer
        self._view.show()
        self._view.hud.hide()
        
        # create countdown to to start timer
        self._countdown = SemaphoreTimer(3)
        self._countdown.start()
    
    @eventCallback
    def start(self):
        logger.info("Starting game")
        
        self._view.hud.show()
        self._startTimer()
        
        self._gameIsAlive = True
        
        f1 = Wait(2)
        f2 = Func(self._countdown.destroy)
        Sequence(f1,f2).start()
        
        
    def restart(self):
        logger.info("Restarting game")
        
        # reset the ball 
        pos = self._getStartingPos()
        self._ball.nodepath.setPos(render, pos)
        self._ball.nodepath.setHpr(0,0,0)
        self._ball.physics.speed = 0
        self._ballCtrl.nodepath.setPosHpr(self._ball.nodepath.getPos(),
                                          self._ball.nodepath.getHpr())
        
        self._ballZ = self._ball.nodepath.getZ() + 0.2 # track height
        
        # set again the current segment to the first one
        self._setupTrackCollision()
        
        # reset the cp delegate
        self._cpDelegate.startPos = pos
        self._cpDelegate.latestCp = pos
        
        self._collHandler.clear()
        
        self._startTimer()
    
    def endTrack(self):
        logger.info("Track finished")
        
        self._view.timer.stop()
        self._ball.slowDown()
        
        # reset the orientation of the camera otherwise 3D objects in the
        # menus will appear shifted. The camera is a child of ballCtrl.
        self._resetBallPos()
        
    def update(self, task):
        if self._gameIsAlive:
            dt = globalClock.getDt()
            self._updateDelta = dt
            while self._updateDelta > self._updateStep:
                self._updateDelta -= self._updateStep
            
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
            
            
            # TODO put this in an update method in the ball class
            root = self._ballCtrl.nodepath.getParent()
            forward = root.getRelativeVector(self._ballCtrl.nodepath,Vec3(0,1,0)) 
            forward.setZ(0)
            forward.normalize()
            
            speedVec = forward * dt * self._ball.physics.speed
            self._ball.physics.speedVec = speedVec
            
            self._ballCtrl.nodepath.setPos(self._ballCtrl.nodepath.getPos() + speedVec)
            self._ballCtrl.nodepath.setZ(self._ballZ + self._ball.jumpZ + \
                                      self._ball.physics.radius)
            
            # rotate the _ball
            self._ball.nodepath.setP(self._ball.nodepath.getP() -1 * dt * \
                                      self._ball.physics.speed * 
                                      self._ball.physics.spinningFactor)
            # set the _ball to the position of the controller node
            self._ball.nodepath.setPos(self._ballCtrl.nodepath.getPos())
            # rotate the controller to follow the direction of the _ball
            self._ballCtrl.nodepath.setH(self._ball.nodepath.getH())
            
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
            # TODO make the special item disappear for three seconds
            # do not remove it ! if the player falls he may restart before the item
            # hence he may pick it up again.
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
        self._simDelta += globalClock.getDt()
        while self._simDelta > self._simStep:
            self._simDelta -= self._simStep
        
        return task.cont
    
    def collisionStep(self, task):
        if self._gameIsAlive:
            # run collisions only once every self._collStep seconds (1/60)
            self._collDelta += globalClock.getDt()
            while self._collDelta > self._collStep:
                self._collDelta -= self._collStep
            
            self._picker.traverse(self._currentSegment)
            self._ballCollNodeNp.setQuat(self._track.nodepath,Quat(1,0,0,0))
        
        return task.cont
    
    def updateProfile(self):
        # TODO shouldn't be here but in gamesession
        info = GS.getTrackInfo(GS.selectedTrack)
        
        timer = self._view.timer 
        
        result = TrackResult()
        result.bestTime = info.limit - timer.elapsedTime
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
    
    def destroy(self):
        self._listener.ignoreAll()
        self._listener = None
        
    @eventCallback
    def _onTimeOver(self):
        logger.info("Time's up, restarting track")
        
        messenger.send(event.RESTART_TRACK)
        
    @eventCallback
    def _onBallIntoCheckpoint(self, entry):
        if self._gameIsAlive:
            logger.info("Checkpoint crossed")
            
            cp = entry.getIntoNodePath()
            self._cpDelegate.latestCp = cp
            self._cpDelegate.segment = self._currentSegment
        
    @eventCallback
    def _onBallIntoSpecialTile(self, tile ,entry):
        if self._gameIsAlive:
            logger.info("Ball on special tile")
            
            self._tileType = tile
        
    @eventCallback
    def _onBallIntoSpecialItem(self, item ,entry):
        if self._gameIsAlive:
            logger.info("Ball on special item")
            
            self._ball.setSpecialitem(item)
        # TODO remove also node, get it from entry
    
    @eventCallback
    def _onBallOutSegment(self, entry):
        if self._gameIsAlive:
            into = entry.getIntoNodePath().getParent()
            
            logger.info("Ball out of %s" % into.getName())
            
            if self._isSegment(into):
                self._currentSegment.setCollideMask(BitMask32.allOff())
                
                seg = self._track.getNextSegment(self._currentSegment)
                if not seg.isEmpty():
                    num = self._track.getSegmentNum(seg)
                    self._currentSegment = seg.getParent()
                    self._currentSegment.setCollideMask(BitMask32(1))
                    
                    self._listener.ignore("ray-again-segment_%d" % (num-1)) 
                    self._listener.accept("ray-again-segment_%d" % num, 
                                          self._onBallAgainSegment) 
                    self._listener.accept("ray-out-segment_%d" % num,
                                          self._onBallOutSegment) 
                    
                    if seg.hasNetTag("end-point"):
                        messenger.send(event.END_TRACK)
                        
    @eventCallback
    def _onBallAgainSegment(self, entry):
        if self._gameIsAlive:
            z = entry.getSurfacePoint(render).getZ()
            self._ballZ = z
        
    def _loadTrack(self, tid):
        # TODO remove first existing track from scene
        
        logger.info("Using track %s" % tid)
        
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/tracks/%s.track"% tid) ,".", 
                  VirtualFileSystem.MFReadOnly)
        
        if self._track is not None:
            self._track.nodepath.removeNode()
        self._track = GOM.getEntity(entity.new_track_params, False)
        
        self._track.nodepath.ls()
        self._setupTrackCollision()
        
        outsides = self._track.nodepath.findAllMatches("**/outside*")
        for outside in outsides:
            outside.show()
        
    
    def _setupTrackCollision(self):
        segs = self._track.nodepath.findAllMatches("**/segment*")
        
        # set bitmasks and bind events for the first segment
        self._currentSegment = segs[0].getParent()
        self._currentSegment.setCollideMask(BitMask32(1))
        self._listener.accept("ray-out-segment_0" , self._onBallOutSegment)
        self._listener.accept("ray-again-segment_0" , self._onBallAgainSegment)
        
        # checkpoints 
        # TODO change name, tile is too ambiguos and has nothing to do with cp
        self._cpDelegate.segment = self._currentSegment
        
        tiles = self._track.nodepath.findAllMatches("**/tile")
        for tile in tiles:
            tile.setCollideMask(BitMask32.allOff())
        cps = self._track.nodepath.findAllMatches("**/cp")
        for cp in cps:
            cp.setCollideMask(BitMask32(1))

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
        # HACK 4 is almost half segment(5), unless the segment is a curve :/
        pos = self._getStartingPos()
        self._ball.nodepath.setPos(render, pos)
        
        # the first checkpoint is the starting position
        self._cpDelegate.startPos = pos
        
        # this is the node that control the ball, it is always oriented in
        # the same direction so I can use it to determine the forward vector
        # of the ball as it's not rolling.
        self._ballCtrl = GOM.getEntity(entity.player_params)
        self._ballCtrl.nodepath.setPos(self._ball.nodepath.getPos())
        self._ballCtrl.nodepath.setQuat(self._track.nodepath,Quat(1,0,0,0))
        self._ball.forward = Vec3(0,1,0)
        
        # z value of the ball, this is updated every frame.
        self._ballZ = self._ball.nodepath.getZ()
        
        # make the ball collide. I can't do it in setupCollision 'cause the ball
        # doesn't exists yet at that point
        self._ballCollNodeNp = self._ball.nodepath.attachCollisionRay(
                                                   "ray",
                                                   0,0,10, # origin
                                                   0,0,-1, # direction
                                                   BitMask32(1), #into
                                                   BitMask32.allOff())
        self._ballCollNodeNp.show()
        # orient it perpendicular to the track
        self._ballCollNodeNp.setQuat(self._track.nodepath, Quat(1,0,0,0))
        self._picker.addCollider(self._ballCollNodeNp, self._collHandler)
        
    def _playBallFallingSequence(self, entry=None):
        # play falling sequence and restart from latest 
        # checkpoint (or start point)
        logger.info("Falling...")
        self._ballCtrl.nodepath.setPos(self._cpDelegate.startPos)
        self._ball.nodepath.setPos(self._cpDelegate.startPos)
        
        #time.sleep(1)
        
        # TODO the current segment must be updated too
        self._currentSegment = self._cpDelegate.segment
        self._currentSegment.setCollideMask(BitMask32(1))
        
        # XXX Panda generates a ray-out-<current_segment> event as soon as I 
        # move the ball into the current_segment. Another weird behavior of this
        # collision system ...
        self._collHandler.clear()
        
        self._ball.physics.speed = 0
        
        """
        sp = self._cpDelegate.startPos
        startPos = Point3(sp[0], sp[1], sp[2])
        if self._cpDelegate.latestCp is not None:
            startPos = self._cpDelegate.latestCp
        seq = Sequence(Func(self.__setattr__,"_gameIsAlive",False), 
                       Func(self._ball.getLost, startPos),
                       Func(self.__setattr__,"_gameIsAlive",True),
                       Func(self._ballCtrl.nodepath.setPos, 
                            self._ball.nodepath.getPos()),
                       Func(self._listener.acceptOnce, 
                             "ray-into-outside-right", 
                             self._playBallFallingSequence),
                       Func(self._listener.acceptOnce, 
                             "ray-into-outside-left", 
                             self._playBallFallingSequence))
        seq.start()
        """        
        
    def _getStartingPos(self):
        t = self._track.nodepath.find("**/=start-point")
        pos = map(lambda x: float(x), t.getTag("start-point").split(","))
        
        return (pos[0], pos[1]-4, pos[2])
    
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
        self._picker = CollisionTraverser()
        
        self._collHandler = CollisionHandlerEvent()
        self._collHandler.addInPattern("ray-into-%in")
        
        # XXX for some very odd reasons, these allow "out" and "again"
        #  collisions with all the segments and not only for the first one (0)
        self._collHandler.addOutPattern("ray-out-segment_0")
        self._collHandler.addAgainPattern("ray-again-segment_0")
    
    def _isSegment(self, node):
        return node.getName().startswith("segment")
    
    def _subscribeToEvents(self):
        # TODO put names in event file
        # Ball events
        #messenger.toggleVerbose()
        
        do = DirectObject()
        do.accept("ray-into-outside_right", self._playBallFallingSequence)
        do.accept("ray-into-outside_left", self._playBallFallingSequence)
        do.accept(event.BALL_INTO_CHECKPOINT, self._onBallIntoCheckpoint)
        do.accept(event.BALL_INTO_SLOW, self._onBallIntoSpecialTile, ["slow"])
        do.accept(event.BALL_INTO_ACCELERATE, self._onBallIntoSpecialTile, 
                  ["accelerate"])
        do.accept(event.BALL_INTO_JUMP, self._onBallIntoSpecialTile, ["jump"])
        
        do.accept(event.TIME_OVER, self._onTimeOver)
        
        # other events
        do.accept(event.COUNTDOWN_END, self.start)
        
        self._listener = do
        
    def _startTimer(self):
        info = GS.getTrackInfo(GS.selectedTrack)
        timer = self._view.hud.timer
        #timer.stop()
        timer.addTime(info.limit)
        timer.start()
    
    def _resetBallPos(self):
        self._ball.nodepath.setHpr(0,0,0)
        self._ballCtrl.nodepath.setHpr(0,0,0)
        

class GameApplication(object):

    dta = 0
    stepSize = 1/60.0

    def __init__(self):
        singleton(self)
        super(GameApplication, self).__init__()
        
        GS.setApplication(self)
        
        self._listener = SafeDirectObject()
        
        if self._checkRequirements():
            
            # stop the collision loop, I have my own.
            taskMgr.remove("collisionLoop")
            
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
    
    @eventCallback
    def restartRace(self):
        GS.state.request(GameState.RESTART)
    
    def startProcesses(self):
        logger.debug("Starting processes")
        taskMgr.add(self._game.inputMgr.update, "update-input")
        taskMgr.add(self._game.collisionStep, "collision-step")
        taskMgr.add(self._game.update, "update-objects")
        # nothing to do for now
        #taskMgr.add(self._game.simulationStep, "world-simulation")
        
    def stopProcesses(self):
        logger.debug("Stopping processes")
        taskMgr.remove("update-input")
        taskMgr.remove("collision-step")
        taskMgr.remove("world-simulation")
        taskMgr.remove("update-objects")
    
    def createGameAndView(self):
        # TODO first destroy (or reset) previous game and view if they exists
        logger.debug("Creating game and view")
        
        if hasattr(self, "_view"):
            self._view.destroy()
        if hasattr(self, "_game"):
            self._game.destroy()
        
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
        self._listener.accept(event.RESTART_TRACK, self.restartRace)
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
            self.a = 0
            self._game._track.nodepath.show()
    
    def _createWindow(self):
        self._wp = WindowProperties().getDefault()
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
    
    