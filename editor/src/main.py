# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
License: BSD

This module is
"""

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import Point3, Vec4, Vec3, NodePath
from pandac.PandaModules import LightAttrib, AmbientLight, DirectionalLight

from sys import exit
from random import randint, seed
seed()

from mdlib.panda import loadModel
from mdlib.panda.camera import CameraManager

BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
RED = Vec4(1,0,0,1)
GREEN = Vec4(0,1,0,1)
BLUE = Vec4(0,0,1,1)
HIGHLIGHT = Vec4(1,1,0.3,0.5)

colors = [BLACK,WHITE,RED,GREEN,BLUE]

masterNode = render.attachNewNode("master")

class GameEntity(object):
    def __init__(self, path, parent, scale, pos, debug=0):
        self.nodePath = loadModel(loader, path, parent, scale, pos)
        self.debug = debug
        
        #self.nodePath.showTightBounds()
     
    def getNodePath(self):
        return self.nodePath
       
    def getPos(self):
        return self.nodePath.getPos()

class Cell(GameEntity):
    LENGTH = 2
    HEIGHT = .2

    def __init__(self, path, parent, pos, debug=0):
        super(Cell, self).__init__(path, parent, 1, pos, debug)
        self.nodePath.setColor(colors[randint(0,len(colors)-1)])
    

class InputSystem(DirectObject):
    def __init__(self):
        DirectObject.__init__(self)
    
    def bind(self, key, command, options = []):
        self.accept(key, command, options)

class Track():
    cells = []
    ROW_LENGTH = 5
    
    def __init__(self):
        self.trackNP = masterNode.attachNewNode("track")
    
    def addRow(self):
        for i in range(0, self.ROW_LENGTH):
            self.addCell()
    
    def addCell(self):
        # by default put a new cell close to the latest added
        if len(self.cells) > 0:
            prevPos = self.cells[-1].getPos()
            if len(self.cells) % self.ROW_LENGTH == 0: 
                incX = - (self.ROW_LENGTH-1) * Cell.LENGTH
                incY = Cell.LENGTH
            else:
                incX = Cell.LENGTH
                incY = 0
            pos = Point3(prevPos.getX() + incX, prevPos.getY()+ incY, prevPos.getZ())
        else:
            pos = Point3(0,0,1)
        
        cell = Cell("../res/cell", masterNode, pos)
        self.cells.append(cell)
        
class World(object):
    entities = []
    track = Track()
    
    def __init__(self):
        self._prepareWorld()
        self._setupLights()
    
    def addRow(self):
        self.track.addRow()
        
    def addCell(self):
        self.track.addCell()
        
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
        
    def _prepareWorld(self):
        env = GameEntity("../res/environment", masterNode, 0.25, Point3(-8,42,-5))
        self.entities.append(env)
        

class Editor(object):
    ins = InputSystem()

    def __init__(self):
        self.world = World()
        self.cameraMgr = CameraManager(self.ins)

        self.ins.bind("escape", self.quit)
        self.ins.bind("space", self.world.addCell)
        self.ins.bind("shift-space", self.world.addRow)
        
        self.isRunning = True
    
    def quit(self):
        self.isRunning = False
    
    def run(self):
        import time
        while self.isRunning:
            time.sleep(0.1)
            taskMgr.step()
        else:
            # TODO do cleanup
            print "quitting..."

if __name__ == "__main__":
    e = Editor()
    e.run()
    