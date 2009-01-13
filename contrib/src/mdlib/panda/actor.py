# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

An Actor is an object the player can interact with and/or moves.
The actor contains all the informations about the object, for ex.
its size, the number of lives left, its position, textures and
materials etc.. 
 
All these properties are stored in the Params class, which is read from
disk in order to change an Actor without modifying the source code.

The only information the Actor doesn't contain, is the scene node.
This property is exclusive of the corresponding Entity. This is because
an Actor may exists but not be attached (yet) to a scene.  

All the properties of the Actor are created during the instantiation of the
object EXCEPT the geometry which is set once the PhysicManager is done
calculating it. 

TODO: add Antialiasing and Transparency attributes

"""

from mdlib.panda.physics import BOX_GEOM_TYPE, SPHERE_GEOM_TYPE
from pandac.PandaModules import Vec4, BitMask32, Quat, Point3

previous_id = 0
def id_generator():
    global previous_id
    id = previous_id
    previous_id += 1
    return id

class AbstractActor(object):
    """ Base Actor class """
    def __init__(self, params):
        self.params = params
    
    def update(self):
        if self.geom != None:
            self.params.position = Point3(self.geom.getPosition())
            self.params.rotation = Quat(self.geom.getQuaternion())
    
    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self.params.__dict__[attr]
       
    def __repr__(self):
        return "Actor %s #%s" % (self.__class__.__name__, self._id)
    
    ID = property(fget=lambda self: self._id, fset=None)
    position = property(fget=lambda self: self.params.position, 
                        fset=lambda self,pos:setattr(self.params,"position",pos))
    rotation = property(fget=lambda self: self.params.rotation, 
                        fset=lambda self,rot:setattr(self.params,"rotation",rot))


class AbstractParams(object):
    def __init__(self):
        self._id = id_generator()


class CellActor(AbstractActor):
    """ The CellActor is the actor that represents a cell on a Track """
    pass

class CellParams(AbstractParams):
    def __init__(self):
        global COLOR_IDX
        
        super(CellParams, self).__init__()
        # for the sake of testing let's put some params here
        # without reading them from disl
        self.collisionBitMask = BitMask32.bit(1)#(0x00000001)
        self.categoryBitMask = BitMask32.allOff()#(0x00000001) #2
        self.geomType = BOX_GEOM_TYPE 
        self.density = -1
        self.length = 2.0
        self.width = 2.0
        self.height = 0.2
        self.modelPath = "cell_normal"
        self.scale = 1
        self.position= (0,0,0)
        self.rotation= (0,0,0,0)
        self.hasBody = False
        self.geom = None
        self.parentNode = None
        self.posTag = ""


class EnvironmentParams(AbstractParams):
    def __init__(self):
        super(EnvironmentParams, self).__init__()
        
        self.modelPath = "environment"
        self.scale = 0.25
        self.position = Point3(-8,42,-5)
        self.rotation = (0,0,0,0)
        self.hasBody = False
        self.geom = None
        self.parentNode = None

class TheBallActor(AbstractActor):
    """
    TheBall is, essentially, a ball.
    It can move left and right, it can rotate forward and decelerate in order
    to stop, but can't *accelerate* backward. It can move backward if a force
    pushes it in that direction.
    """
    pass


class TheBallParams(AbstractParams):
    def __init__(self):
        super(TheBallParams, self).__init__()
        
        self.modelPath = "golf-ball"
        self.scale = 1
        self.position = Point3(4,2,10)
        self.rotation = Quat(1,0,0,0)
        self.geomType = SPHERE_GEOM_TYPE 
        self.hasBody = True
        self.density = 400
        self.linearSpeed = 3000
        self.collisionBitMask = BitMask32.bit(1)
        self.categoryBitMask = BitMask32.bit(1)
        self.xForce = 0
        self.yForce = 0
        self.zForce = 0
        self.torque = 0
        self.radius = 0.56
        
