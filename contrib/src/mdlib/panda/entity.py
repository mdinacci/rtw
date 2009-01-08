# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

An entity exists only in a Scene and it has a node that bind it into the
scenegraph.
If this entity is animated and has physical properties then a corresponding
object called Actor is created and managed in the game logic.

The parameters needed for the creation of the two objects are shared in 
another object of the type Params

Ex. 
- BallEntity -> 3D representation, model, light, materials, textures etc..  
- BallActor  -> logic and physical representation: radius, density, lifes etc.
- BallParams -> contains shared parameters: id and what else ?

The parameters are created in the logic, then an event is sent in order for 
the entity object to be properly initialised. The entity is then inserted into
the scene. Parameters are read from disk, in order to change more easily the
properties of the objects.


TODO 

use FSM to switch between the various entity states
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("entity", DEBUG)

from direct.task.Task import Task

from mdlib.panda import loadModel, pandaCallback, SafeDirectObject
from mdlib.decorator import Property, deprecated
from mdlib.panda import math

from pandac.PandaModules import Point3, Vec4, BitMask32, Quat
from pandac.PandaModules import AntialiasAttrib

# to randomly choose a color
from random import randint, seed
seed()


__all__=["EnvironmentEntity", "CellEntity", "TheBallEntity"]


class GameEntity(object):
    """ Base entity class """
    def __init__(self, params):
        self._id = params._id
        self._nodePath = loadModel(loader, params.modelPath, params.parentNode, 
                                   params.scale, Point3(params.position) )
        
        self._nodePath.setTag("ID", str(self._id))
        self.params = params
        
        self.isDirty = False
    
    def _setPosition(self, position):
        self.params.position = position
        self._nodePath.setPos(position)
    
    def _setRotation(self, rotation):
        self.params.rotation = rotation
        self._nodePath.setPos(rotation)
        
    def serialise(self):
        pass
    
    def unserialise(self):
        pass
    
    def update(self):
        """ Update this actor position in the world """
        self._nodePath.setPosQuat(Point3(self.params.position), 
                                  math.vec4ToQuat(self.params.rotation))
    
    def __repr__(self):
        return "%s ID: %s" % (self.__class__.__name__, self._id)
        
    ID = property(fget=lambda self: self._id, fset=None)
    nodePath = property(fget=lambda self: self._nodePath, fset=None)
        

class CellEntity(GameEntity):
    """ This entity represents a 3D cell in a track """
    
    def __init__(self, params):
        super(CellEntity, self).__init__(params)
        self._nodePath.setColor(params.color)
        self._nodePath.setTag("pos", params.posTag) # XXX :/
        
    def __repr__(self):
        return "Cell #%s at %s" % (self._id, self._nodePath.getTag("pos"))
    
    def changeNature(self, nature):
        newCell = loader.loadModel("cell_%s" % nature.lower())
        if newCell is not None:
            logger.info("Changing cell nature to: %s" % nature)
            newCell.setScale(self._nodePath.getScale())
            newCell.setPos(self._nodePath.getPos())
            parent = self._nodePath.getParent()
            newCell.setTag("pos",self._nodePath.getTag("pos"))
            newCell.setColor(self._nodePath.getColor())
            self._nodePath.removeNode()
            
            newCell.reparentTo(parent)
            self._nodePath = newCell
        else:
            logger.error("Cannot change nature cell to: %s. Model does not \
            exist." % nature )


class EnvironmentEntity(GameEntity): 
    """ This entity represents the background elements """
    
    def update(self):
        pass


class TheBallEntity(GameEntity):
    """ This entity represents the player character. """
    
    pass

    
class EntityManager(object):
    """ 
    The entity manager provide a safe and easy way to load, save and
    delete entities from the application. Entities can be loaded from a 
    directory, from a file or from a Panda3D Multifile. 
    """
    previous_id = -1
    
    @staticmethod
    def id_generator():
        global previous_id
        id = previous_id
        previous_id += 1
        return id
    
    def __init__(self):
        self.input = SafeDirectObject()
        self.input.accept("delete-entity", self.deleteEntity)
        
    def deleteEntity(self, entity):
        logger.debug("deleting entity %s in EntityManager" % entity)
    
    def loadEntityFromDir(self, dir):
        pass
    
    def loadEntityFromMultifile(self, dir):
        pass 
    
    def loadEntityFromFile(self, filename): 
        id = EntityManager.id_generator()
