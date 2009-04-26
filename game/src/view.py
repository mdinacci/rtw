# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG, INFO
logger = ConsoleLogger("view", DEBUG)

from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence

from pandac.PandaModules import DirectionalLight, AmbientLight, NodePath, Fog,\
PointLight, Vec4, Camera, WindowProperties, LightNode, Shader, Point3, \
PandaNode, LightRampAttrib, Vec3, Vec4, TextNode

from direct.filter.CommonFilters import CommonFilters

from mdlib.panda.core import AbstractScene

import event

__all__ = ["GameView", "Camera", "HUD", "RaceTimer"]


class GameScene(object):
    def __init__(self):
        self._rootNode = NodePath("root")
        self._rootNode.reparentTo(render)
        self.hide()
        
        self._setupLightsAndFog()
    
    def show(self):
        self._rootNode.show()
        
    def hide(self):
        self._rootNode.hide()
    
    def addEntity(self, entity):
        entity.nodepath.reparentTo(self._rootNode)
    
    def _setupLightsAndFog(self):
        dlight = DirectionalLight('dlight')
        alight = AmbientLight('alight')
        dlnp = self._rootNode.attachNewNode(dlight)
        alnp = self._rootNode.attachNewNode(alight)
        dlight.setColor(Vec4(0.7, 0.7, 0.6, 1))
        alight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        dlnp.setHpr(0, -60, 0)
        self._rootNode.setLight(dlnp)
        self._rootNode.setLight(alnp)
        
        colour = (0.2,0.2,0.2)
        expfog = Fog("fog")
        expfog.setColor(*colour)
        expfog.setExpDensity(0.001)
        self._rootNode.setFog(expfog)
        
    root = property(fget=lambda self: self._rootNode)
        

class GameView(object):
    def __init__(self):
        self._hud = HUD()
        self._cam = Camera()
        self._scene = GameScene()
    
    def showCursor(self, show = True):
        logger.debug("Toggling cursor")
        props = WindowProperties()
        props.setCursorHidden(not show)
        base.win.requestProperties(props)
    
    def show(self):
        logger.debug("Showing view")
        self._hud.show()
        self._scene.show()
    
    def hide(self):
        logger.debug("Hiding view")
        self._hud.hide()
        self._scene.hide()
        
    def _setupScene(self):
        pass

    cam = property(fget=lambda self: self._cam)
    scene = property(fget=lambda self: self._scene)
    hud = property(fget=lambda self: self._hud)
    timer = property(fget=lambda self: self._hud.timer)
    

class Camera(object):
    ZOOM = 30
    TARGET_DISTANCE = 13
    
    def __init__(self):
        base.disableMouse()
        base.camera.setPos(0,0,0)
        pl =  base.cam.node().getLens()
        pl.setFov(33)
        pl.setFar(pl.getFar()/3)
        base.cam.node().setLens(pl) 
    
    def followTarget(self, target):
        self.target = target
        base.camera.reparentTo(target.nodepath)
        base.camera.setPos(0, -18, 10)
        base.camera.lookAt(target.nodepath, Point3(0,10,0))
    
    def attachCollisionRay(self, *args):
        return base.camera.attachCollisionRay(*args)
    
    def getQuat(self):
        return base.camera.getQuat()
    
    def getPos(self):
        return base.camera.getPos()
    
    def update(self):
        pass


class HUD(object):
    def __init__(self):
        self.timer = RaceTimer(True)
    
    def show(self):
        logger.debug("Showing HUD")
        self.timer.timerText.show()
    
    def hide(self):
        logger.debug("Hiding HUD")
        self.timer.timerText.hide()
    
        
class RaceTimer(object):
    def __init__(self, countdown=False):
        self._countdown = countdown
        self._isPaused = False
        
        self.elapsedTime = 0
        self.time = "0:0.0"
        if self._countdown:
            self.textScale = .15
            self.timerText = OnscreenText(text="%s" % self.time, style=1, 
                              fg=(1,1,1,1),pos=(-0.05,.85),shadow= (1,0,0,.8), 
                              scale = self.textScale, mayChange=True, 
                              align=TextNode.ALeft)
        else:
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
        logger.debug("Starting timer")
        name = "timer-task"
        func = self.update
        if self._countdown:
            name = "countdown-task"
            func = self.updateCountdown
            
        taskMgr.doMethodLater(0.1, func, name)
    
    def togglePause(self):
        logger.debug("Timer toggle pause")
        
        name = "timer-task"
        func = self.update
        if self._countdown:
            name = "countdown-task"
            func = self.updateCountdown
            
        if self._isPaused:
            taskMgr.doMethodLater(0.1, func, name)
            self._isPaused = False
        else:
            taskMgr.remove(name)
            self._isPaused = True
    
    def reset(self):
        self.time = "0:0.0"
        self.elapsedTime = 0
    
    def stop(self):
        logger.debug("Stopping timer")
        
        name = "timer-task"
        if self._countdown:
            name = "countdown-task"
            
        taskMgr.remove(name)
    
    def addTime(self, tenths):
        self.elapsedTime += tenths
        
    def removeTime(self, tenths):
        self.elapsedTime -= tenths
    
    def render(self):
        self.timerText.setScale(self.textScale)
        self.timerText.setText(self.time)
    
    def updateCountdown(self, task):
        if self.elapsedTime == 0:
            self.stop()
            self.reset()
            messenger.send(event.TIME_OVER)
        else:
            self.elapsedTime -=1
        
        seconds = self.elapsedTime / 10
        tens = self.elapsedTime % 10
            
        self.time = "%s.%s" % (seconds, tens)
        self.render()
        
        return task.again
    
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
        self.render()
        
        return task.again
