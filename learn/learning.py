# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

In this module:

- Loading a model and creating an actor
- Using intervals
- Using tasks

"""

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "want-directtools 1")
loadPrcFileData("", "want-tk 1")

import direct.directbase.DirectStart
from direct.task import Task
from direct.actor import Actor
from direct.showbase.DirectObject import DirectObject 
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

import math
import sys

from mdlib.panda import loadModel

class World(DirectObject):
    
    def __init__(self):
        pos = Point3(-8,42,0)
        self.environ = loadModel(loader,"models/environment",render, 0.25, pos)
        taskMgr.add(self.SpinCameraTask, "SpinCameraTask")
        self.accept("escape", sys.exit)
        self.accept("m", self.dumpStuff)
        self.accept("shift-m", self.dumpStuff2)
        
    def dumpStuff(self):
        node = render.find("**/environment.egg")
        print node
        node.ls()
        node.removeNode()
        
    def dumpStuff2(self):
        print "in dumpstuff2"
        node = render.find("**/environment.egg")
        print "node is none: ", node is None
        print "---------------------"
        print "node ls: "
        node.ls()
        print "---------------------"
        
        print "---------------------"
        print "environ ls: "
        self.environ.ls()
        print "---------------------"
        
    def SpinCameraTask(self,task):
        angledegrees = task.time * 6.0
        angleradians = angledegrees * (math.pi / 180.0)
        base.camera.setPos(20*math.sin(angleradians),-20.0*math.cos(angleradians),3)
        base.camera.setHpr(angledegrees, 0, 0)
        return Task.cont

    def addPanda(self):
        self.pandaActor = Actor.Actor("models/panda-model",{"walk":"models/panda-walk4"})
        self.pandaActor.setScale(0.005,0.005,0.005)
        self.pandaActor.reparentTo(render)
        self.pandaActor.loop("walk")
        #Create the four lerp intervals needed to walk back and forth
        pandaPosInterval1= self.pandaActor.posInterval(13,Point3(0,-10,0), startPos=Point3(0,10,0))
        pandaPosInterval2= self.pandaActor.posInterval(13,Point3(0,10,0), startPos=Point3(0,-10,0))
        pandaHprInterval1= self.pandaActor.hprInterval(3,Point3(180,0,0), startHpr=Point3(0,0,0))
        pandaHprInterval2= self.pandaActor.hprInterval(3,Point3(0,0,0), startHpr=Point3(180,0,0))
        
        #Create and play the sequence that coordinates the intervals
        pandaPace = Sequence(pandaPosInterval1, pandaHprInterval1,
                             pandaPosInterval2, pandaHprInterval2, name = "pandaPace")
        pandaPace.loop()


    def main(self):
        run()
        

if __name__ == "__main__":
    w = World()
    w.addPanda()
    w.main()
