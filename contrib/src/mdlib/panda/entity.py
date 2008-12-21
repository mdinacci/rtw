# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("entity", DEBUG)

from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task

from mdlib.panda import loadModel, pandaCallback
from mdlib.decorator import Property

from pandac.PandaModules import Point3, Vec4, BitMask32

# to randomly choose a color
from random import randint, seed
seed()

# some colors
BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
RED = Vec4(1,0,0,1)
GREEN = Vec4(0,1,0,1)
BLUE = Vec4(0,0,1,1)
HIGHLIGHT = Vec4(1,1,0.3,0.5)
colors = [BLACK,WHITE,RED,GREEN,BLUE]

previous_id = -1
def id_generator():
    global previous_id
    id = previous_id
    previous_id += 1
    return id

class GameEntity(object):
    """ 
    Basic entity of the game 
    TODO: pos, quat and density must be properties
    """
    def __init__(self):
        self._id = id_generator()

    def __repr__(self):
        return "%s ID: %s" % (self.__class__.__name__, self._id)
        
    def getNodePath(self):
        return self._nodePath
       
    def getPos(self):
        return self._nodePath.getPos()
    
    def getQuat(self):
        return self._nodePath.getQuat()
    
    ID = property(fget=lambda self: self._id, fset=None)
    
    
class GameActor(GameEntity):
    """  
    A game actor is different from a GameEntity in the sense that
    it can physically interact with the world.
    It is usually represented by a 3D model and has physical properties. 
    """
    
    BOX_GEOM_TYPE = "box"
    SPHERE_GEOM_TYPE = "sphere"
    
    def __init__(self, path, parent, scale, pos):
        super(GameActor, self).__init__()
        self._nodePath = loadModel(loader, path, parent, scale, pos)
        self._setupPhysics()

    def _setupPhysics(self):
        self._density = 400
        self._body = None
        self._geomType = None
    
    def hasBody(self):
        """ 
        An actor can have a physical geometry but no body, 
        which basically means that it can be used for collision
        detection but it is not affected by physical properties
        """
        return True
    
    def getBody(self):
        """ Returns the physical representation of this actor """
        return self._body
    
    def setBody(self, body):
        self._body = body
    
    def getGeometryType(self):
        return self._geomType
    
    def getDensity(self):
        # FIXME to integrate in the "physic body"
        return self._density
    
    def getCollisionBitMask(self):
        return self._collisionBitMask
    
    def getCategoryBitMask(self):
        return self._categoryBitMask
    
    def update(self, pos, quat):
        self.getNodePath().setPosQuat(pos,quat)


class Cell(GameActor):
    length = 2.0
    width = 2.0
    height = 0.2

    def __init__(self, parent, pos):
        super(Cell, self).__init__("cell", parent, 1, pos)
        self.getNodePath().setColor(colors[randint(0,len(colors)-1)])
     
    def hasBody(self):
        return False
     
    def getBody(self):
        return None
        
    def _setupPhysics(self): 
        self._collisionBitMask = BitMask32.bit(1)#(0x00000001)
        self._categoryBitMask = BitMask32.allOff()#(0x00000001) #2
        self._geomType = GameActor.BOX_GEOM_TYPE 
        self._density = -1 # a Cell has no body so density doesn't matter


class Environment(GameActor):
    def __init__(self, parent, pos):
        super(Environment, self).__init__("environment", parent, 0.25, pos)
     
    def hasBody(self):
        return False
     
    def getBody(self):
        return None

class Track(GameEntity):
    _cells = []
    ROW_LENGTH = 5
    
    def __init__(self, parent):
        super(Track, self).__init__()
        self._nodePath = parent.attachNewNode("track")
    
    def getCellAtIndex(self, idx):
        if idx < len(self._cells):
            return self._cells[idx]
        else:
            logger.error("Cell %d doesn't exists !" % idx)
    
    def getCells(self):
        return self._cells
    
    def addRow(self):
        for i in range(0, self.ROW_LENGTH):
            self.addCell()
    
    def addCell(self):
        cell = self._createCell()
        self._cells.append(cell)
        messenger.send("entity-new", [cell])
        
    def _createCell(self):
        # by default put a new cell close to the latest added
        if len(self._cells) > 0:
            prevPos = self._cells[-1].getPos()
            if len(self._cells) % self.ROW_LENGTH == 0: 
                incX = - (self.ROW_LENGTH-1) * Cell.length
                incY = Cell.length
            else:
                incX = Cell.length
                incY = 0
            pos = Point3(prevPos.getX() + incX, prevPos.getY()+ incY, prevPos.getZ())
        else:
            pos = Point3(0,0,1)
        
        cell = Cell(self._nodePath, pos)
        
        # set row, column tag; it makes easy to identify the cell after
        cellNP = cell.getNodePath()
        row = (len(self._cells)) / (self.ROW_LENGTH)
        col = (len(self._cells)) % (self.ROW_LENGTH)
        cellNP.setTag("pos", "%d %d" % (row,col))
        logger.debug("Adding cell at row,col (%d,%d)" % (row,col))
        
        return cell
        
class TheBall(GameActor):
    radius = 0.56
    
    def __init__(self, parent, pos):
        super(TheBall, self).__init__("golf-ball", parent, 1, pos)
        self._setupPhysics()
        taskMgr.add(self._move, "Move Ball")
    
    @pandaCallback    
    def _move(self, task):
        # TODO just apply a force now, later we have to 
        # check that the user doesn't go backward and that
        # we don't go to fast !
        body = self.getBody()
        body.addForce(self._xForce, self._yForce, self._zForce)

        return Task.cont
    
    def _setForce(self, xForce, yForce, zForce):
        self._xForce = xForce * self._linearSpeed
        self._yForce = yForce * self._linearSpeed
        self._zForce = zForce * self._linearSpeed
            
    def _setupPhysics(self): 
        self._density = 600
        self._linearSpeed = 8000
        self._collisionBitMask = BitMask32.bit(1)#allOff()
        self._categoryBitMask = BitMask32.bit(1)#(0x00000001)
        self._geomType = GameActor.SPHERE_GEOM_TYPE
        self._xForce = 0
        self._yForce = 0
        self._zForce = 0
        self._torque = 0
    
    def update(self, pos, quat):
        np = self.getNodePath()
        np.setPosQuat(pos, quat)
        
