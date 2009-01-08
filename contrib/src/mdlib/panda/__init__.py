# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is a collection of utilities to use while developing
a Panda3D program

"""
import os

from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import Vec4

class Color(object):
    # some colors
    BLACK = Vec4(0,0,0,1)
    WHITE = Vec4(1,1,1,1)
    RED = Vec4(1,0,0,1)
    GREEN = Vec4(0,1,0,1)
    BLUE = Vec4(0,0,1,1)
    HIGHLIGHT = Vec4(1,1,0.3,0.5)
    
    COLOR_IDX = 0
    b_n_w = [BLACK,WHITE]

# TODO move to input
class SafeDirectObject(DirectObject):
    def destroy(self):
        self.ignoreAll() 

# TODO check for model existance, if not raise ModelNotFoundException
def loadModel(loader, path, parentNode, scale, pos):
    model = loader.loadModel(path)
    model.setScale(scale)
    model.setPos(pos)
    model.reparentTo(parentNode)
    return model
    
def groupNodes(render, groupName, *nodes):
    groupNode = render.attachNewNode(groupName)
    for node in nodes:
        node.reparentTo(groupNode)
    
    return groupNode


# DECORATORS

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

class ModelNotFoundException(Exception):
    def __init__(self, modelPath):
        super(ModelNotFoundException, self).__init__("Model %s not found" % modelPath)
        
    