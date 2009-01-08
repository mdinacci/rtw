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
        base.buttonThrowers[0].node().setButtonDownEvent('button')
        base.buttonThrowers[0].node().setButtonUpEvent('buttonUp')
        self.accept("button", self._onButtonDown)
        self.accept("buttonUp", self._onButtonUp)
        
        self.accept("escape", sys.exit)
        self.accept("event-test", self.getEvent)

    def _onButtonDown(self, key):
       print "button down: %s " % key
        
    def _onButtonUp(self, key):
       print "button up: %s " % key
        
    def getEvent(self, foo, bar):
        print foo, bar

    def main(self):
        run()

if __name__ == "__main__":
    
    w = World()
    messenger.send("event-test",["ciccio", "pasticcio"])
    w.main()