# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

In this demo:

- Importing models into a scene 
- Colors
- Picking 3D objects using collision rays
- Writing text on screen
- Reacting to keyboard and mouse events

"""

import direct.directbase.DirectStart
from direct.actor import Actor
from direct.showbase.DirectObject import DirectObject 
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *
from direct.task.Task import Task

import sys
from mdlib.panda import loadModel
from random import randint

BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
RED = Vec4(1,0,0,1)
GREEN = Vec4(0,1,0,1)
BLUE = Vec4(0,0,1,1)
HIGHLIGHT = Vec4(1,1,0.3,0.5)

colors = [BLACK,WHITE,RED,GREEN,BLUE]

class PickedObjectState(object):
    color = BLACK = Vec4(0,0,0,1)
    index = -1

class World(DirectObject):
    cols = 5
    rows = 200
    
    def __init__(self):
        self.title = OnscreenText(text="Demo 2",
                              style=1, fg=(1,1,1,1),
                              pos=(0.8,-0.95), scale = .07)
        
        #base.oobe()
        #Allow manual positioning of the camera
        base.disableMouse()
        camera.setPosHpr ( 0, -15, 3.5, 0, 0, 0 )
     
        self._createPlane()
        self._loadModels()
        self._setupCollisionDetection()
        #self.setupLights()
        self.accept("escape", sys.exit)
        self.accept("w", self.moveForward)
        self.accept("s", self.moveBackward)
        self.accept("a", self.moveWest)
        self.accept("d", self.moveEast)
        self.accept("mouse1", self._onMousePress)
        
    def __hasSelection(self):
        return hasattr(self, "pickedObjectState")
        
    def _onMousePress(self):
        if base.mouseWatcherNode.hasMouse():
            mousePos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mousePos.getX(), mousePos.getY())
            self.picker.traverse(self.track)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                
                if self.__hasSelection():
                    previousIndex = self.pickedObjectState.index
                    previousColor = self.pickedObjectState.color
                    self.squares[previousIndex].setColor(previousColor)
                    self.squares[previousIndex].setRenderModeFilled()
                else:
                    self.pickedObjectState = PickedObjectState()
                    
                pickedObject = self.pq.getEntry(0).getIntoNodePath()
                print "object: " , pickedObject
                print "row,col: ", pickedObject.getNetTag("pos")
                row, col = map(lambda x: int(x), pickedObject.getNetTag("pos").split())
                idx = row*self.cols+col
                
                self.pickedObjectState.color = self.squares[idx].getColor()
                self.pickedObjectState.index = idx
                
                self.squares[idx].setColor(HIGHLIGHT)
                self.squares[idx].setRenderModeWireframe()

    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        #self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
    def moveForward(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX(), p.getY()+4.0, p.getZ()))

    def moveBackward(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX(), p.getY()-4.0, p.getZ()))
        
    def moveWest(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX()-2, p.getY(), p.getZ()))
        
    def moveEast(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX()+2, p.getY(), p.getZ()))
    
    def _createPlane(self):
        self.track = render.attachNewNode("track")
        self.squares = [None for i in range(0,self.cols*self.rows)]
        
        for j in range(0, self.rows):
            for i in range(0, self.cols):
                square = loader.loadModelCopy("models/square") 
                square.reparentTo(self.track)
                
                abs_idx = j*self.cols+i
                
                pos = Point3(( abs_idx % self.cols)-2, int( abs_idx /self.cols), 2)
                square.setPos(pos)
                square.setColor(colors[randint(0,len(colors)-1)])
                square.setTag("pos", "%d %d" % (j,i))
                self.squares[abs_idx] = square
                

    def _loadModels(self):
        self.env = loader.loadModel("models/env")
        self.env.reparentTo(render)
        self.env.setScale(100)

    def _setupLights(self):
        #Create some lights and add them to the scene. By setting the lights on
        #render they affect the entire scene
        #Check out the lighting tutorial for more information on lights
        lAttrib = LightAttrib.makeAllOff()
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(.4, .4, .35, 1) )
        lAttrib = lAttrib.addLight( ambientLight )
        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setDirection( Vec3( 0, 8, -2.5 ) )
        directionalLight.setColor( Vec4( 0.9, 0.8, 0.9, 1 ) )
        lAttrib = lAttrib.addLight( directionalLight )
        render.attachNewNode( directionalLight.upcastToPandaNode() )
        render.attachNewNode( ambientLight.upcastToPandaNode() )
        render.node().setAttrib( lAttrib )
    
        #Explicitly set the environment to not be lit
        lAttrib = LightAttrib.makeAllOff()
        self.env.node().setAttrib( lAttrib )

    def main(self):
        run()
        

if __name__ == "__main__":
    w = World()
    w.main()
