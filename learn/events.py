# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>

This module is
"""

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject

import sys

class World(DirectObject):
    def __init__(self):
        self.accept("escape", sys.exit)
        self.accept("event-test", self.getEvent)
        
    def getEvent(self, foo, bar):
        print foo, bar

    def main(self):
        run()

if __name__ == "__main__":
    
    w = World()
    messenger.send("event-test",["ciccio", "pasticcio"])
    w.main()