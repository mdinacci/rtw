# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module is a collection of utilities to use while developing
a Panda3D program

"""

import os

# TODO check for model existance, if not raise ModelNotFoundException
def loadModel(loader, path, parentNode):
    model = loader.loadModel(path)
    model.reparentTo(parentNode)
    return model
    
def groupNodes(render, groupName, *nodes):
    groupNode = render.attachNewNode(groupName)
    for node in nodes:
        node.reparentTo(groupNode)
    
    return groupNode


class ModelNotFoundException(Exception):
    def __init__(self, modelPath):
        super(ModelNotFoundException, self).__init__("Model %s not found" % modelPath)
        
    