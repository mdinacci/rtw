# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Code to deal with user input, via mouse, keyboard and joysticks
"""

from mdlib.log import ConsoleLogger, DEBUG, INFO
logger = ConsoleLogger("input", INFO)

from pandac.PandaModules import ModifierButtons
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task

import event

BASE_SCHEME = "base"

__all__ = ["SafeDirectObject", "Command", "InputScheme", "InputManager", 
           "BASE_SCHEME"]


class SafeDirectObject(DirectObject):
    def destroy(self):
        self.ignoreAll() 

class Command(object):
    """
    A Command can be either an Event or a Callback. An event is sent using the
    event manager while the callback is executed directly. The command also
    stores arguments and the key used to fire it. 
    """
    
    EVENT = 0x1
    CALLBACK = 0x2
    
    def __init__(self, name, type, args=[]):
        self.name= name
        self.args = args
        self.pressed = False
        self.type = type
        
    def __repr__(self):
        s = "%s name:\t %s\n args:\t %s\n pressed:\t %s\n type:\t %s\n"\
            % (self.__class__.__name__, self.name, self.args, self.pressed, self.type)
        return s

class InputScheme(object):
    """ 
    An InputScheme is a sequence of commands that can be enabled or disabled
    in the InputManager. 
    """
    def __init__(self, name):
        self._name = name
        self._enabled = True
        self._commands = {}
    
    def __repr__(self):
        return self._name
    
    def getCommands(self):
        return self._commands  
    
    def __repr__(self):
        return "Name: %s" % (self._name)
    
    name = property(fget=lambda self: self._name, fset=None)
    

class InputWatcher(object):
    """ An InputWatcher receives raw input events from the InputManager """
    
    def acceptUp(self, key):
        pass
    
    def acceptDown(self, key):
        pass
    
        
class InputManager(SafeDirectObject):
    """
    The InputManager class manage all the input coming from the player and
    send events according to the pressed buttons.
    
    It supports multiple InputScheme where a scheme is basically a map
    of commands. 
    There is a special input scheme, the BASE_SCHEME scheme, whose values are
    always checked. It is a sort of global input scheme whose commands are
    always executed.
    
    Each key can be bound to an unlimited number of commands.
    """
    
    def __init__(self, disableAlt=False):
        
        # get rid of alt button
        if disableAlt:
            self.disableAlt()
            
        base.buttonThrowers[0].node().setButtonDownEvent('button')
        base.buttonThrowers[0].node().setButtonUpEvent('buttonUp')
        base.buttonThrowers[0].node().setButtonRepeatEvent('buttonRepeat')
        
        self.accept("button", self._onButtonDown)
        self.accept("buttonRepeat", self._onButtonRepeat)
        self.accept("buttonUp", self._onButtonUp)
        
        self._currentScheme = InputScheme(BASE_SCHEME)
        self._schemes = {BASE_SCHEME: self._currentScheme}
        self._lastCmdTime = 0
        self._watchers = []
    
    
    def disableAlt(self):
        buttons = base.mouseWatcherNode.getModifierButtons()
        if buttons.getNumButtons() > 2:
            buttons.removeButton(buttons.getButton(2))
            base.mouseWatcherNode.setModifierButtons(buttons)
            base.buttonThrowers[0].node().setModifierButtons(buttons)
        
    def addWatcher(self, watcher):
        self._watchers.append(watcher)

    def removeWatcher(self, watcher):
        if watcher in self._watchers:
            self._watchers.remove(watcher)
    
    def switchSchemeTo(self, name):
        if name in self._schemes.keys():
            logger.info("Switching to scheme: %s" % name)
            self._currentScheme = self._schemes[name]
        else:
            logger.warning("Can't switch to non existent scheme: %s" % name)
    
    def createScheme(self, name):
        logger.info("Creating scheme: %s " % name)
        scheme = InputScheme(name)
        self._schemes[name] = scheme
    
    def createSchemeAndSwitch(self, name):
        self.createScheme(name)
        self.switchSchemeTo(name)
    
    def getCurrentScheme(self):
        return self._currentScheme
    
    def update(self, Task = None):
        """ 
        Check pressed keys and send corresponding events. 
        XXX The problem with this approach is that events are sent only 
        on button down, not on button up. For the moment this is not
        a problem but it can become troublesome in the future
        """
        commands = self._currentScheme.getCommands().values() + \
            self._schemes[BASE_SCHEME].getCommands().values()
        
        for commandList in commands:
            for command in commandList:
                if command.pressed is True:
                    command.pressed = False
                    if command.type == Command.EVENT:
                        logger.debug("Sending message %s with args  %s" 
                                     % (command.name, command.args))
                        messenger.send(command.name, command.args)
                    elif command.type == Command.CALLBACK:
                        logger.debug("Executing callback %s with args  %s" 
                                     % (command.name.__name__, command.args))
                        command.name(*command.args)
                        
        return Task.cont
    

    def bind(self, key, cmdName, cmdType, args=[], schemeName=BASE_SCHEME):
        scheme = self._schemes[schemeName]
        if not scheme.getCommands().has_key(key):
            if logger.isEnabledFor(DEBUG):
                name = ""
                if callable(cmdName):
                    name = cmdName.__name__
                else:
                    name = cmdName
                logger.debug("Binding key %s in scheme %s to %s %s with args %s"\
                             % (key, scheme, cmdType, name, args))
            scheme.getCommands()[key] = [Command(cmdName, cmdType, args)]
        else:
            logger.debug("Adding new command to key %s " % key)
            scheme.getCommands()[key].append(Command(cmdName, cmdType, args))
            
    
    def bindEvent(self, key, name, args=[], scheme=None):
        if scheme is None:
            scheme = self._currentScheme.name
        self.bind(key, name, Command.EVENT, args, scheme)
            
    def bindCallback(self, key, callback, args=[], scheme=None):
        if scheme is None:
            scheme = self._currentScheme.name
        self.bind(key, callback, Command.CALLBACK, args, scheme)
    
    def _onButtonDown(self, key):
        logger.debug("Button %s pressed" % key)
        if key in self._currentScheme.getCommands().keys():
            for command in self._currentScheme.getCommands()[key]:
                command.pressed = True
        elif key in self._schemes[BASE_SCHEME].getCommands().keys():
            for command in self._schemes[BASE_SCHEME].getCommands()[key]:
                command.pressed = True
        
    def _onButtonRepeat(self, key):
        logger.debug("Button %s repeated" % key)
        if key in self._currentScheme.getCommands().keys():
            for command in self._currentScheme.getCommands()[key]:
                command.pressed = False
        elif key in self._schemes[BASE_SCHEME].getCommands().keys():
            for command in self._schemes[BASE_SCHEME].getCommands()[key]:
                command.pressed = False
        
    def _onButtonUp(self, key):
        logger.debug("Button %s up" % key)
        
        for watcher in self._watchers:
            watcher.acceptUp("%s-%s" % (key, "up"))
        
        # certain keys can consist of multiple combination of buttons
        # for instance shift-x. The problem here is that there is no event
        # "shift-x-up" so the command will never be terminated. 
        # To fix this problem, I take the keys and look if they are prefixed 
        # by special keys (shift, meta etc...); if they are, I set the 
        # command off when the x key is up.
        
        keys = self._currentScheme.getCommands().keys()
        for k in keys:
            # key is of the type <special>-key
            if "-" in k:
                first, second = k.split("-")
                if first in ("space", "meta", "alt", "ctrl", "win"):
                    k = k[k.index("-")+1:]
        
        # Turn off button down
        if key in keys:
            for command in self._currentScheme.getCommands()[key]:
                command.pressed = False
        if key in self._schemes[BASE_SCHEME].getCommands().keys():
            for command in self._schemes[BASE_SCHEME].getCommands()[key]:
                command.pressed = False
        
        # Turn on key up, which is turned off in the update method
        key = "%s-up" % key
        if key in keys:
            for command in self._currentScheme.getCommands()[key]:
                command.pressed = True
        if key in self._schemes[BASE_SCHEME].getCommands().keys():
            for command in self._schemes[BASE_SCHEME].getCommands()[key]:
                command.pressed = True
                
        self.keyUp = key
     