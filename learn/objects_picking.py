# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is
"""

import direct.directbase.DirectStart
from direct.task import Task
from direct.actor import Actor
from direct.showbase.DirectObject import DirectObject 
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import *

from mdlib.panda import loadModel

class World(DirectObject):
    
    def __init__(self):
        environ = loadModel(loader,"models/environment",render)
        environ.setScale(0.25,0.25,0.25)
        environ.setPos(-8,42,0)
        taskMgr.add(self.SpinCameraTask, "SpinCameraTask")
        self.accept("escape", sys.exit)

    def main(self):
        run()
        

if __name__ == "__main__":
    w = World()
    w.main()
