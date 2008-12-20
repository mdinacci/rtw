# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is a collection of utilities to use while developing
a Panda3D program

"""
import os

from direct.showbase.DirectObject import DirectObject

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

def pandaCallback(fn):
    """ 
    A decorator which does absolutely nothing but document
    that a function is a callback called from Panda3D  
    """
    def new(*args):
        # do nothing for the moment
        return fn(*args)
    return new

class ModelNotFoundException(Exception):
    def __init__(self, modelPath):
        super(ModelNotFoundException, self).__init__("Model %s not found" % modelPath)
        
    