# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

In this module:

- Loading a model and creating an actor
- Using intervals
- Using tasks

"""

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
        environ = loadModel(loader,"models/environment",render)
        environ.setScale(0.25,0.25,0.25)
        environ.setPos(-8,42,0)
        taskMgr.add(self.SpinCameraTask, "SpinCameraTask")
        self.accept("escape", sys.exit)
        
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
