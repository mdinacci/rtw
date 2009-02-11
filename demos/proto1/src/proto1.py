# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import loadPrcFile
loadPrcFile("../res/Config.prc")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject

from pandac.PandaModules import Point3

from mdlib.panda.camera import RoamingCamera
from mdlib.panda.input import SafeDirectObject, InputManager
from mdlib.panda.data import GOM
from mdlib.panda.physics import POM
from mdlib.panda.core import AbstractScene
from mdlib.panda.entity import ball_params, new_track_params, tile_params

import sys

base.wireframeOn()

class World(AbstractScene):
    def __init__(self):
        super(World, self).__init__()
        self._rootNode.reparentTo(render)
        
        self.input = InputManager(base)
        self.camera = RoamingCamera(self.input)
        self.camera.setPos(0, -20, 10)
        self.camera.lookAt(0,10,0)
        self.camera.linearSpeed = 5
        
        self.createEntities()
        
        self.input.bindCallback("escape", sys.exit, scheme="base")
        self.input.bindCallback("0", self.camera.lookAtOrigin)
        self.input.bindCallback("1", self.showBounds)
        self.idx = 0
        
    
    def showBounds(self):
        self.segments[self.idx].reparentTo(render)
        self.segments[self.idx].showTightBounds()
        self.idx +=1

    def createEntities(self):
        self.track = GOM.createEntity(new_track_params)
        
        n = self.track.render.nodepath
        
        self.segments = n.findAllMatches("**/segment*").asList()
        self.segments.reverse()
        
        for seg in self.segments:
            tile = GOM.createEntityFromNodepath(seg, tile_params.copy())
            self.track.addTile(tile)
        #self.addEntity(self.track)
        
        #ball_params["position"]["x"] = 0
        #ball_params["position"]["y"] = 80
        #ball_params["position"]["z"] = 0
        #self.ball = GOM.createEntity(ball_params)
        
        #self.addEntity(self.ball)
        

    def updateTask(self, task):
        self.input.update()
        self.camera.update()
        self.update()
        POM.update(self)
        
        return task.cont
        
    def run(self):
        taskMgr.add(self.updateTask, "update-all")
        run()


if __name__ == '__main__':
    
    #a = GOM.createEntity(new_track_params)
    #n = a.render.nodepath
    #print n.findAllMatches("**/*").asList()
    
    w = World()
    w.run()