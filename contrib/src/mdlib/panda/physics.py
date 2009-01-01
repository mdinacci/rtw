# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("physics", DEBUG)

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject

from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdeSphereGeom, BitMask32

class EntityGeom(object):
    def __init__(self, space, entityID):
        self.ID = entityID
        # FIXME this must be removed, geoms should be 
        # explicitely added to the spacewith space.add(geom)
        if type(space) is EntitySpace:
            space.add(self)
        else:
            logger.error("Space must be an instance of EntitySpace")

class EntityBoxGeom(OdeBoxGeom, EntityGeom):
    def __init__(self, space, length, width, height, entityID):
        OdeBoxGeom.__init__(self, length, width, height)
        EntityGeom.__init__(self, space, entityID)


class EntitySphereGeom(OdeSphereGeom, EntityGeom):
    def __init__(self, space, radius, entityID):
        OdeSphereGeom.__init__(self, radius)
        EntityGeom.__init__(self, space, entityID)

        
class EntitySpace(OdeSimpleSpace):
    """
    This space is simply an OdeSimpleSpace but 
    GameEntity aware. It allows to retrieve a geometry given
    the entity ID
    FIXME this is no good, the geometry should be stored inside
    the entity and then to remove it from the space it must be
    a matter of doing a getGeom() on the entity and space.remove(geom)
    """
    def __init__(self):
        super(EntitySpace, self).__init__()
        # entity ID -> geometry index
        self.lookupTable = {}
        self.__idx = 0
    
    def add(self, entity):
        """ 
        Add a new entity to the space
        This method is overridden in order to store the entity ID
        """
        super(EntitySpace, self).add(entity)
        self.lookupTable[entity.ID] = self.__idx
        self.__idx+=1
    
    def getGeometryForEntityID(self, entityID):
        """ 
        Returns the geometry given the entity ID 
        
        ODE puts new geometries to the front of the list so the 
        correct index is: len(list) - lookupTable_idx 
        """
        return self.getGeom(len(self.lookupTable)-self.lookupTable[entityID])
        
        