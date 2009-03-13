# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import loadPrcFile
loadPrcFile("../res/Config.prc")

from mdlib.panda import config as cfg
cfg.loadFile("options.prc")

#from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart

from pandac.PandaModules import *

from direct.gui.OnscreenText import OnscreenText
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import *
from direct.task.Task import Task
from direct.fsm import FSM

from mdlib.panda.entity import *
from mdlib.panda.core import *
from mdlib.panda.data import GOM
from mdlib.panda.input import *
from mdlib.panda.utils import *
from mdlib.types import Types
from mdlib.panda import event

from mdlib.patterns import singleton

import sys, math

from gui import *

#base.wireframeOn()

class Camera(object):
    ZOOM = 30
    TARGET_DISTANCE = 13
    
    def __init__(self):
        base.accept('wheel_up-up', self.zoomIn)
        base.accept('wheel_down-up', self.zoomOut)
        base.disableMouse()
        base.camera.setPos(0,0,0)
        pl =  base.cam.node().getLens()
        pl.setFov(33)
        pl.setFar(pl.getFar()/3)
        base.cam.node().setLens(pl) 
    
    def showCursor(self, show = True):
        """ Hide the mouse cursor """
        props = WindowProperties()
        props.setCursorHidden(not show)
        base.win.requestProperties(props)
          
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

        z = self.target.physics.jumpZ
        base.camera.setZ(self.target.nodepath.getZ() -z + 3)
        pos = self.target.nodepath.getPos()
        pos.setZ(pos.getZ() -z)
        base.camera.lookAt(pos)
        base.camera.setZ(self.target.nodepath.getZ() -z + 5)
    

HEIGHT_TRACK = 0.0

class GameLogic(AbstractLogic):
    DUMMY_VALUE = -999
    
    # the view is not really the view but just the scene for now.
    def __init__(self, view):
        super(GameLogic, self).__init__(view)
        
        self.env = GOM.createEntity(environment_params)
        self.view.addEntity(self.env)
        
        self._setupEntities()
        self._setupLights()
        
        # HACK
        self.view.track = self.track

        self.cam = Camera()
        self.camGroundZ = -999
        self.view.cam = self.cam
        
        self.lastTile = ""
        self.tileType = "neutral"
        self.lastTileType = "neutral"
        
        
        colour = (0.2,0.2,0.2)
        expfog = Fog("fog")
        expfog.setColor(*colour)
        expfog.setExpDensity(0.001)
        self.track.nodepath.setFog(expfog)
        base.setBackgroundColor(*colour)
    
        self.controlInverted = False
    
    def setupBall(self, ball):
        params = ballsMap[ball]
        self.ball = GOM.createEntity(params)
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
        self.cam.followTarget(self.ball)
        
        # HACK
        self.view.player = self.player
        self.view.ball = self.ball
        
        self.ball.nodepath.setShaderAuto()
        from direct.filter.CommonFilters import CommonFilters
        filters = CommonFilters(base.win, base.cam)
        #filters.setCartoonInk(separation=2)
        filters.setBloom(blend=(0.0,0.0,0.6,0), desat=-0.5, intensity=1.0)
        self._setupCollisionDetection()
        
     
    def _setupLights(self):   
        dlight = DirectionalLight('dlight')
        alight = AmbientLight('alight')
        dlnp = render.attachNewNode(dlight)
        alnp = render.attachNewNode(alight)
        dlight.setColor(Vec4(0.6, 0.6, 0.9, 1))
        alight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        dlnp.setHpr(0, -60, 0)
        render.setLight(dlnp)
        render.setLight(alnp)

    
    def _setupEntities(self):
        self.track = GOM.createEntity(new_track_params)
        self.track.unfold()
        self.track.nodepath.setCollideMask(BitMask32(1))
        #self.track.nodepath.setAntialias(AntialiasAttrib.MLine)
        self.view.addEntity(self.track)
                
        
    def updatePhysics(self, task):
        dt = globalClock.getDt()
        
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
                    rootNode = np.getParent().getParent().getParent()
                    if rootNode.hasTag("effect"):
                        self.ball.setSpecialItem(rootNode.getTag("effect"))
                        rootNode.removeNode()
                    else:    
                        # tell the track which segment the ball is on
                        self.track.setCurrentTile(np)
                        
                        # find out the tile type from the texture
                        textures = np.findAllTextures()
                        if textures.getNumTextures() > 1:
                            self.tileType = textures.getTexture(1).getName()
                        else:
                            self.tileType = textures.getTexture(0).getName()
                        #self.tileType = np.findAllTextures().getTexture(0).getName()
                    
                    self.ball.RayGroundZ = z
                    
                    ballIsCollidingWithGround = True
                    if entry != self.lastTile:
                        self.lastTile = entry
                        
            self.camGroundZ = firstGroundContact
        
        if ballIsCollidingWithGround == False:
            if self.ball.isJumping():
                print "no ball-ground contact but jumping"
            else:
                print "no ball-ground contact, losing"
                self.ball.getLost()
                self.view.gameIsAlive = False
                return Task.done # automatically stop the task
        
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
        speedVec = forward * dt * self.ball.physics.speed
        self.ball.forward = forward
        self.ball.physics.speedVec = speedVec

        self.player.nodepath.setPos(self.player.nodepath.getPos() + speedVec)
        self.player.nodepath.setZ(self.ball.RayGroundZ + 
                                  self.ball.physics.jumpZ + \
                                  self.ball.physics.radius + HEIGHT_TRACK)
           
        # rotate the ball
        self.ball.nodepath.setP(self.ball.nodepath.getP() -1 * dt * \
                                  self.ball.physics.speed * 
                                  self.ball.physics.spinningFactor)
        # set the ball to the position of the controller node
        self.ball.nodepath.setPos(self.player.nodepath.getPos())
        # rotate the controller to follow the direction of the ball
        self.player.nodepath.setH(self.ball.nodepath.getH())
        
        return Task.cont
    
    
    def resetGame(self):
        self.player.nodepath.setPos(Point3(6,0,0))
        self.ball.nodepath.setPos(Point3(6,0,0))
        self.ball.nodepath.setQuat(Quat(1,0,0,0))
        self.ball.physics.speed = 0

        self.view.gameIsAlive = True
        self.view.time = "0:0.0"
    
    
    def updateLogic(self, task):
        
        # steer
        
        if self.keyMap["right"] == True:
            if self.ball.physics.speed > 0:
                if self.controlInverted:
                    self.ball.turnLeft()
                else:
                    self.ball.turnRight()
            
        if self.keyMap["left"] == True:
            if self.ball.physics.speed > 0:
                if self.controlInverted:
                    self.ball.turnRight()
                else:
                    self.ball.turnLeft()
        
        if self.keyMap["forward"] == True:
            if self.controlInverted:
                self.ball.brake()
            else:
                self.ball.accelerate()
        else:
            self.ball.decelerate()
        
        if self.keyMap["backward"] == True:
            if self.controlInverted:
                self.ball.accelerate()
            else:
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
        elif self.tileType == "freeze":
            if self.lastTileType != "freeze":
                self.ball.freeze()
        else:
            print "unknown type: " , self.tileType
        
        self.lastTileType = self.tileType
        
        # special items
        if self.ball.hasSpecialItem():
            item = self.ball.specialItem
            if item == "M":
                self.ball.minimize()
            elif item == "I":
                self.ball.invisibleMode()
            elif item == "+":
                self.view.raceTimer.addTime(30)
                self.view.raceTimer.flash()
            elif item == "-":
                self.view.raceTimer.removeTime(30)
                self.view.raceTimer.flash()
            elif item == "?":
                delay = Wait(3)
                f = Func(self.__setattr__,"controlInverted", True)
                f1 = Func(self.__setattr__,"controlInverted", False)
                Sequence(f, delay, f1).start()
                
                
            self.ball.specialItem = None
        
        if self.ball.physics.speed < 0:
            self.ball.physics.speed = 0
            
        return Task.cont
    
    
    def setKey(self, key, value):
        self.keyMap[key] = value
    
        
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
        
    
    def endTrack(self):
        self.ball.slowDown()
        self.view.raceTimer.stop() 
    
    def _subscribeToEvents(self):
        base.accept(event.END_TRACK, self.endTrack)
        
        self.keyMap = {"left":False, "right":False, "forward":False, \
                       "backward":False, "jump": False}
        
        self.inputMgr = InputManager(base)
        self.inputMgr.createSchemeAndSwitch("game")
        
        self.inputMgr.bindCallback(cfg.strValueForKey("options_steer_left"), 
                                   self.setKey, ["left",True], scheme="game")
        self.inputMgr.bindCallback(cfg.strValueForKey("options_steer_right"), 
                                   self.setKey, ["right",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_accelerate")
                                   , self.setKey, ["forward",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_brake"), 
                                   self.setKey, ["backward",True])
        self.inputMgr.bindCallback(cfg.strValueForKey("options_jump"), 
                                   self.setKey, ["jump",True])
        
        key = cfg.strValueForKey("options_steer_left") + "-up"
        self.inputMgr.bindCallback(key, self.setKey, ["left",False])
        key = cfg.strValueForKey("options_steer_right") + "-up"
        self.inputMgr.bindCallback(key, self.setKey, ["right",False])
        key = cfg.strValueForKey("options_accelerate") + "-up"
        self.inputMgr.bindCallback(key, self.setKey, ["forward",False])
        key = cfg.strValueForKey("options_brake") + "-up"
        self.inputMgr.bindCallback(key, self.setKey, ["backward",False])
        
        self.inputMgr.bindCallback("c", self.view.switchCamera)
        self.inputMgr.bindCallback("o", render.analyze)
        
        
    

class RaceTimer(object):
    def __init__(self):
        self.elapsedTime = 0
        self.time = "0:0.0"
        self.textScale = .08
        self.timerText = OnscreenText(text="%s" % self.time, style=1, 
                              fg=(1,1,1,1),pos=(1.2,0.90),shadow= (1,0,0,.8), 
                              scale = self.textScale, mayChange=True)
    
    def flash(self):
        scaleUp = Func(self.__setattr__, "textScale", 0.12)
        wait = Wait(1)
        scaleDown = Func(self.__setattr__, "textScale", 0.08)
        
        Sequence(scaleUp, wait, scaleDown).start()
        
    def start(self):
        taskMgr.doMethodLater(0.1, self.update, "timer-task")
    
    def stop(self):
        taskMgr.remove("timer-task")
    
    def addTime(self, tenths):
        self.elapsedTime += tenths
        
    def removeTime(self, tenths):
        self.elapsedTime -= tenths
    
    def render(self):
        self.timerText.setScale(self.textScale)
        self.timerText.setText(self.time)
    
    def update(self, task):
        self.elapsedTime +=1
        tens = self.elapsedTime % 10
        seconds = (self.elapsedTime / 10) % 60
        minutes = (self.elapsedTime / 10) / 60
        if tens == 0:
            tens = "0"
        if seconds == 0:
            seconds = "0"
            
        self.time = "%d:%s.%s" % (minutes, seconds, tens)
        
        return task.again


class World(AbstractScene):
    
    def __init__(self):
        super(World, self).__init__()
        
        loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)
        
        self.setSceneGraphNode(render)
        #self._setupLights()
        self.gameIsAlive = True
        
        self.raceTimer = RaceTimer()
        self.raceTimer.start()
        
    
    def update(self, task):
        if self.gameIsAlive:
            self.cam.update()
            self.raceTimer.render()
            
        return Task.cont
        
    
    def switchCamera(self):
        base.oobe()
    
    def _setupLights(self):
        lAttrib = LightAttrib.makeAllOff()
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(10, 10, 10, 0) )
        lAttrib = lAttrib.addLight( ambientLight )
        render.attachNewNode( ambientLight.upcastToPandaNode() )
        render.node().setAttrib( lAttrib )
        

class ApplicationState(FSM.FSM):
    
    def __init__(self, app):
        FSM.FSM.__init__(self, "app")
        self.app = app
        self.screenMgr = ScreenManager()
        
    def enterExit(self):
        if self.oldState == "Game":
            self.app.scene.cam.showCursor(True)
        taskMgr.remove("update-input")
        taskMgr.remove("update-logic")
        taskMgr.remove("update-physics")
        self.screenMgr.displayScreen("exit")
    
    def exitExit(self):
        self.screenMgr.destroyCurrent()
        if self.oldState == "Menus":
            self.app.show()
        elif self.oldState == "Game":
            taskMgr.add(self.app.logic.inputMgr.update, "update-input")
            taskMgr.add(self.app.logic.updatePhysics, "update-physics")
            taskMgr.add(self.app.logic.updateLogic, "update-logic")
        
    def enterMenus(self):
        render.hide()
        self.screenMgr.displayScreen("main")
        
    def exitMenus(self):
        if self.newState == "Exit":
            self.screenMgr.currentScreen.hide()
        else:
            self.screenMgr.destroyCurrent()
    
    def enterDestroy(self):
        self.app.destroy()
        
    def exitDestroy(self):
        pass
    
    def enterPause(self):
        taskMgr.remove("update-input")
        taskMgr.remove("update-logic")
        taskMgr.remove("update-physics")
        taskMgr.remove("update-scene")
        self.app.scene.cam.showCursor(True)
        self.screenMgr.displayScreen("pause")
    
    def exitPause(self):
        taskMgr.add(self.app.logic.inputMgr.update, "update-input")
        taskMgr.add(self.app.logic.updateLogic, "update-logic")
        taskMgr.add(self.app.logic.updatePhysics, "update-physics")
        taskMgr.add(self.app.scene.update, "update-scene")
        self.app.scene.cam.showCursor(False)
    
    def enterGame(self):
        if not self.app.gameCreated: 
            self.app.scene = World()
            self.app.logic = GameLogic(self.app.scene)
            self.app.logic.setupBall(self.app._selectedBall)
            self.app.scene.cam.showCursor(False)
            self.app.gameCreated = True
        
        taskMgr.add(self.app.logic.inputMgr.update, "update-input")
        taskMgr.add(self.app.logic.updateLogic, "update-logic")
        taskMgr.add(self.app.logic.updatePhysics, "update-physics")
        taskMgr.add(self.app.scene.update, "update-scene")
        
        render.show()
    
    def exitGame(self):
        taskMgr.remove("update-input")
        taskMgr.remove("update-logic")
        taskMgr.remove("update-physics")
        taskMgr.remove("update-scene")
        #self.app.shutdown()
        

class GameApplication(AbstractApplication):

    dta = 0
    stepSize = 1/60.0

    def __init__(self):
        super(GameApplication, self).__init__()
        
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/scene.mf"),".",VirtualFileSystem.MFReadOnly)
        
        wp = WindowProperties().getDefault()
        wp.setOrigin(0,0)
        wp.setFullscreen(cfg.boolValueForKey("options_fullscreen"))
        if not wp.getFullscreen():
            w,h = cfg.strValueForKey("options_resolution").split("x")
            wp.setSize(int(w),int(h))
        base.openDefaultWindow(startDirect=False, props=wp)
        
        self.state = ApplicationState(self)
        self.inputMgr = InputManager(base)
        self.inputMgr.createScheme("app")
        
        self.gameCreated = False
        
    def startGame(self):
        self.state.request("Game")

    def pauseGame(self):
        self.state.request("Pause")

    def unpauseGame(self):
        self.state.request("Off")

    def exitGame(self):
        self.state.request("Exit")

    def destroyGame(self):
        self.state.request("Destroy")
        
    def showOptionsMenu(self):
        self.state.request("OptionsMenu")

    def setSelectedBall(self, ball):
        self._selectedBall = ball

    def _subscribeToEvents(self):
        base.accept("escape", self.pauseGame)
        base.accept("start-game", self.startGame)
        base.accept("exit-game", self.exitGame)
        base.accept("destroy-game", self.destroyGame)
        base.accept(event.RESTART_TRACK, self.restartTrack)
        base.accept(event.UNPAUSE_GAME, self.unpauseGame)
        base.accept(event.PROFILE_MENU_REQUEST, self.destroyGame)
        base.accept(event.OPTIONS_MENU_REQUEST, self.showOptionsMenu)
        base.accept(event.BALL_SELECTED, self.setSelectedBall)
        
    
    def _createLogicAndView(self):
        pass
    
    def continueGame(self):
        self.state.request("")
    
    def restartTrack(self):
        self.logic.resetGame()
        self.state.request("Game")
    
    def show(self):
        self.state.request("Menus")
        taskMgr.run()

    def destroy(self):
        import sys
        sys.exit()
   
     
"""             
# set a fixed frame rate 
from pandac.PandaModules import ClockObject
FPS = 70
globalClock = ClockObject.getGlobalClock()
globalClock.setMode(ClockObject.MLimited)
globalClock.setFrameRate(FPS)
"""    

if __name__ == '__main__':
    GameApplication().show()
    
    #run()    