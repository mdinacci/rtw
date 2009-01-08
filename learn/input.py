# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.task import Task

class Command(object):
    def __init__(self, name, args=[]):
        self.name= name
        self.args = args
        self.fired = False

class Test(DirectObject):
    def __init__(self):
        base.buttonThrowers[0].node().setButtonDownEvent('button')
        base.buttonThrowers[0].node().setButtonUpEvent('buttonUp')
        self.accept("button", self.butt)
        self.accept("buttonUp", self.buttUp)
        
        self.commands = {}
        self.commands["a"] = Command("moveLeft")
        taskMgr.add(self.update, "update")
    
    def update(self, task):
        print "IN update"
        for command in self.commands.values():
            if command.fired is True:
                messenger.send(command.name, command.args)
        return Task.cont
       
    def butt(self, key):
        if key in self.commands.keys():
            self.commands[key].fired = True
        
    def buttUp(self, key):
        if key in self.commands.keys():
            self.commands[key].fired = False
        

 
class Listener(DirectObject):
    def __init__(self):
        self.accept("moveLeft", self.blabla)
    
    def blabla(self):
        print "event received"
        import sys
        sys.exit()
        
t = Test()   
l = Listener()
run()