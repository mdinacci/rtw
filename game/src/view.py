# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence

from pandac.PandaModules import DirectionalLight, AmbientLight, NodePath, Fog
from pandac.PandaModules import Vec4, Camera, WindowProperties, LightNode
from pandac.PandaModules import Shader, Point3, PandaNode


from mdlib.panda.core import AbstractScene


__all__ = ["GameView", "Camera", "HUD", "RaceTimer"]


class GameScene(object):
    def __init__(self):
        self._rootNode = NodePath("root")
        self._rootNode.reparentTo(render)
        self.hide()
        
        self._setupLightsAndFog()
    
    def show(self):
        if 0:
            MYDIR="."
            
            # This shader's job is to render the model with discrete lighting
            # levels.  The lighting calculations built into the shader assume
            # a single nonattenuating point light.
    
            tempnode = NodePath(PandaNode("temp node"))
            tempnode.setShader(Shader.load(MYDIR+"/lightingGen.sha"))
            base.cam.node().setInitialState(tempnode.getState())
            
            # This is the object that represents the single "light", as far
            # the shader is concerned.  It's not a real Panda3D LightNode, but
            # the shader doesn't care about that.
    
            light = render.attachNewNode("light")
            #light.setPos(30,-50,0)
            light.setPos(5,-5,0)
                    
            # this call puts the light's nodepath into the render state.
            # this enables the shader to access this light by name.
    
            render.setShaderInput("light", light)
    
            # The "normals buffer" will contain a picture of the model colorized
            # so that the color of the model is a representation of the model's
            # normal at that point.
    
            normalsBuffer=base.win.makeTextureBuffer("normalsBuffer", 0, 0)
            normalsBuffer.setClearColor(Vec4(0.5,0.5,0.5,1))
            self.normalsBuffer=normalsBuffer
            normalsCamera=base.makeCamera(normalsBuffer, lens=base.cam.node().getLens())
            normalsCamera.node().setScene(render)
            tempnode = NodePath(PandaNode("temp node"))
            tempnode.setShader(Shader.load(MYDIR+"/normalGen.sha"))
            normalsCamera.node().setInitialState(tempnode.getState())
    
            #what we actually do to put edges on screen is apply them as a texture to 
            #a transparent screen-fitted card
    
            drawnScene=normalsBuffer.getTextureCard()
            drawnScene.setTransparency(1)
            drawnScene.setColor(1,1,1,0)
            drawnScene.reparentTo(render2d)
            self.drawnScene = drawnScene
    
            # this shader accepts, as input, the picture from the normals buffer.
            # it compares each adjacent pixel, looking for discontinuities.
            # wherever a discontinuity exists, it emits black ink.
                    
            self.separation = 0.0005
            self.cutoff = 0.05
            inkGen=Shader.load(MYDIR+"/inkGen.sha")
            drawnScene.setShader(inkGen)
            drawnScene.setShaderInput("separation", Vec4(self.separation,0,self.separation,0));
            drawnScene.setShaderInput("cutoff", Vec4(self.cutoff,self.cutoff,self.cutoff,self.cutoff));
        else:
            from direct.filter.CommonFilters import CommonFilters
            #self.filters = CommonFilters(base.win, base.cam)
            #filterok = self.filters.setBloom(blend=(0,0,0,1), desat=-0.5, intensity=3.0, size="small")
                
        
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
        
        """
        colour = (0.2,0.2,0.2)
        expfog = Fog("fog")
        expfog.setColor(*colour)
        expfog.setExpDensity(0.001)
        self._rootNode.setFog(expfog)
        """
        

class GameView(object):
    def __init__(self):
        self._hud = HUD()
        self._cam = Camera()
        self._scene = GameScene()
    
    def showCursor(self, show = True):
        props = WindowProperties()
        props.setCursorHidden(not show)
        base.win.requestProperties(props)
    
    def show(self):
        self._hud.show()
        self._scene.show()
    
    def hide(self):
        self._hud.hide()
        self._scene.hide()
        
    def _setupScene(self):
        pass

    cam = property(fget=lambda self: self._cam)
    scene = property(fget=lambda self: self._scene)
    hud = property(fget=lambda self: self._hud)
    

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
        self.update()
    
    def attachCollisionRay(self, *args):
        return base.camera.attachCollisionRay(*args)
    
    def getQuat(self):
        return base.camera.getQuat()
    
    def getPos(self):
        return base.camera.getPos()
    
    def update(self):
        base.camera.setPos(self.target.nodepath.getPos() - \
                           self.target.forward * self.TARGET_DISTANCE)

        z = self.target.jumpZ
        base.camera.setZ(self.target.nodepath.getZ() -z + 3)
        pos = self.target.nodepath.getPos()
        pos.setZ(pos.getZ() -z)
        base.camera.lookAt(pos)
        base.camera.setZ(self.target.nodepath.getZ() -z + 5)    


class HUD(object):
    def __init__(self):
        self.timer = RaceTimer()
    
    def show(self):
        self.timer.timerText.show()
    
    def hide(self):
        self.timer.timerText.hide()
    
    def startTimer(self):
        self.timer.start()
        
    def stopTimer(self):
        self.timer.stop()

        
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
    
    def resetAndStart(self):
        self.time = "0:0.0"
        self.elapsedTime = 0
        self.start()
        
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
        
        self.render()
        
        return task.again
