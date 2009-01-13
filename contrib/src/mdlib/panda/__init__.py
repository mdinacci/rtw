# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is a collection of utilities useful when developing
a Panda3D program

"""
import os

from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import Vec4

class MouseWatcher(object):
    """ 
    This class monitors whether the mouse is inside the panda window or not. 
    Useful when embedding a Panda3D window in a GUI container.
    """
    def __init__(self, myBase):
        self._myBase = myBase
        self._mouseIsOut = False
        self._outMessageSent = False
        
    def update(self, task=None):
        if not self._myBase.mouseWatcher.node().hasMouse(): 
            self._mouseIsOut = True
            # send the event only once
            if not self._outMessageSent:
                self._myBase.messenger.send(event.MOUSE_LEAVE_PANDA, [None])
                self._outMessageSent = True
        else:
            if self._mouseIsOut:
                self._myBase.messenger.send(event.MOUSE_ENTER_PANDA, [None])
                self._mouseIsOut = False
                self._outMessageSent = False
         
        return task.cont #if task != None: return task.cont


class Color(object):
    """ Some color constants """
    # some colors
    BLACK = Vec4(0,0,0,1)
    WHITE = Vec4(1,1,1,1)
    RED = Vec4(1,0,0,1)
    GREEN = Vec4(0,1,0,1)
    BLUE = Vec4(0,0,1,1)
    HIGHLIGHT = Vec4(1,1,0.3,0.5)
    
    COLOR_IDX = 0
    b_n_w = [BLACK,WHITE]

    
# DECORATORS ===================================================================

def guiCallback(func):
    """ 
    Decorator that documents that the function is called by the GUI 
    in response to the user interacting with a widget. """
    def new(*args):
        return func(*args)
    return new
     
def inputCallback(func):
    """ 
    Decorator that documents that the function is called by the input 
    system in response to a user action. """
    def new(*args):
        return func(*args)
    return new

def eventCallback(func):
    """ 
    Decorator that documents that the function is called by the event 
    system in response to an event just been fired. """
    def new(*args):
        return func(*args)
    return new

def pandaCallback(func):
    """ 
    A decorator which does absolutely nothing but document
    that a function is a callback called from Panda3D  
    """
    def new(*args):
        # do nothing for the moment
        return func(*args)
    return new
