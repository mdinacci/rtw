# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is
"""

import direct.directbase.DirectStart
from direct.task import Task
from direct.actor import Actor
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

import math
#from mdlib.panda import loadModel

class World:
    
    def __init__(self):
        #environ = loadModel(loader,"models/environment",render)
        environ = loader.loadModel("models/environment")
        environ.reparentTo(render)
        environ.setScale(0.25,0.25,0.25)
        environ.setPos(-8,42,0)
        taskMgr.add(self.SpinCameraTask, "SpinCameraTask")
    
    def SpinCameraTask(self,task):
        angledegrees = task.time * 6.0
        angleradians = angledegrees * (math.pi / 180.0)
        base.camera.setPos(20*math.sin(angleradians),-20.0*math.cos(angleradians),3)
        base.camera.setHpr(angledegrees, 0, 0)
        return Task.cont

    def addPanda(self):
        #Load the panda actor, and loop its animation
        pandaActor = Actor.Actor("models/panda-model",{"walk":"models/panda-walk4"})
        pandaActor.setScale(0.005,0.005,0.005)
        pandaActor.reparentTo(render)
        pandaActor.loop("walk")
    
    def main(self):
        run()
        

if __name__ == "__main__":
    w = World()
    w.addPanda()
    w.main()