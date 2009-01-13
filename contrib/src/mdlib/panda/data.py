# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.patterns import singleton

from pandac.PandaModules import *

class ResourceLoader(object):
    """ 
    The ResourceLoader loads and cache resources from disk or network. 
    A Resource can be a 3D model, a texture, a sound, an URL etc...
    """
    def __init__(self):
        # assure there is only one instance of this class
        singleton(self)
        
        self.loader = PandaLoader()
        
    def loadModel(self, path, parentNode, scale, pos):
        """ SYNCHRONOUSLY load a model from disk """
        node = self.loader.loadSync(Filename(path), LoaderOptions())
        if node != None:
            model = NodePath(node)
        else:
            raise ModelNotFoundException()
        model.setScale(scale)
        model.setPos(pos)
        model.reparentTo(parentNode)
        return model


class ModelNotFoundException(Exception):
    def __init__(self, modelPath):
        super(ModelNotFoundException, self).__init__("Model %s not found" % modelPath)
        