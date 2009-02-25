# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("entity", DEBUG)

from mdlib.panda.input import SafeDirectObject
from mdlib.panda.data import GOM, GameEntity, EntityType, \
        KeyValueObject, transformToKeyValue
from mdlib.panda import event
from mdlib.types import Types
from mdlib.panda import utils
from direct.interval.LerpInterval import LerpFuncNS, LerpPosInterval
from direct.interval.IntervalGlobal import Sequence
from direct.interval.FunctionInterval import Wait
from direct.showbase.PythonUtil import Functor

from pandac.PandaModules import NodePath, Point3, OdeGeom, Quat, Material, Vec4


class EntityUpdaterDelegate(object): 
    def updateEntity(self, entity, keypaths):
        logger.debug("Updating entity %s" % entity)
        
        for keypath in keypaths:
            prefix = keypath[:keypath.index(".")]
            
            path = keypath[keypath.index(".")+1:]
            
            if prefix == "physics":
                self.updatePhysics(entity, path)
            elif prefix == "render":
                self.updateRender(entity, path)
            elif prefix == "position":
                self.updatePosition(entity, path)
            else:
                logger.warning("Prefix unrecognized: %s" % prefix)
                
    def updatePhysics(self, entity, path):
        pass
    
    def updatePosition(self, entity, path):
        try:
            pos = entity.position
            quat = entity.position.rotation
        except KeyError, e:
            logger.warning("Entity %s has no position, can't update it" % entity)
            return
        
        if entity.has_key("render") and entity.render.has_key("nodepath"):
            entity.render.nodepath.setPos(Point3(pos.x, pos.y, pos.z))
            #entity.render.nodepath.setQuat(Quat(quat[0], quat[1], 
            #                                    quat[2],quat[3]))
        
        """
        if entity.has_key("physics") and entity.physics.has_key("geom"):
            # just setting both of them is easier and should be faster than
            # calling the functions accordingly to the path
            entity.physics.geom.setPosition(pos.x, pos.y, pos.z)
            #entity.physics.geom.setQuaternion(math.vec4ToQuat(pos.rotation))
        """    
    
    def updateRender(self, entity, path):
        pass


class Track(GameEntity):
    """
    Track is an utility class used to manage and organise groups of cells.
    It reorders the cell in order to have a simpler geometry, it changes
    properties etc.. 
    
    A Track is made of a list of cells, it has a start point and an end point 
    Entities do not collide directly with the Track but with the cells that made
    the track. The track nodes are organized in rows:
    
    track_node
            |___row1
            |     |__cell1
            |     |__cell2
            |     |__cell3
            |     |__cell4
            |     |__cell5
            |
            |___row2
                  |__cell1
            etc...
            
    Once a row has been surpassed, for performance reasons it should be removed
    from the track, as it is forbidden to drive backward. 
    
    TODO squeeze the track after working with it as deleted cells will 
    make the list longer ?.
    """
    
    def __init__(self, uid, data):
        """
        I need the previous cell and the number of cells, no need to store
        the cells here, let's delegate it to the GOM
        """
        super(Track, self).__init__(uid, data)
        self._rows = []
        
    def unfold(self):
        n = self.render.nodepath
        rows = n.findAllMatches("**/row*").asList()
        rows.reverse()
        
        for row in rows:
            ent = GOM.createEntityFromNodepath(row, row_params)
            ent.render.parentNode = int(self.UID)
            self._rows.append(ent)
        
        self.render.nodepath.hide()
        
    
    def serialise(self):
        attrs = super(Track, self).serialise()
        del attrs._tiles
        return attrs

    rows = property(fget=lambda self: self._rows)
    

class Ball(GameEntity):
    MAX_SPEED = 15
    MAX_STEER = 30
    FALLING_SPEED = 250
    FALLING_Z = 5
    
    def __init__(self, uid, data):
        super(Ball, self).__init__(uid, data)
        self.steeringFactor = .5
        self.spinningFactor = 90
        self.jumpHeight = .6
        self.speed = 0
        self.jumpZ = 0
        
        jumpUp = LerpFuncNS(Functor(self.__setattr__,"jumpZ"), 
                    blendType="easeOut",duration=.2, 
                    fromData=self.jumpZ, toData=self.jumpHeight)
        jumpDown = LerpFuncNS(Functor(self.__setattr__,"jumpZ"), 
                      blendType="easeIn",duration=.2, 
                      fromData=self.jumpHeight, toData=0)
        self.jumpingSequence = Sequence(jumpUp, jumpDown, name="jumping")
        
    def setBall(self, ball):
        self.ball = ball
        self.ball.nodepath.setPos(self.nodepath.getPos())
    
    def update(self):
        pass
    
    def turnRight(self):
        currentH = self.nodepath.getH()
        self.nodepath.setH(currentH - self.steeringFactor)
    
    def turnLeft(self):
        currentH = self.nodepath.getH()
        self.nodepath.setH(currentH + self.steeringFactor)
    
    def isJumping(self):
        return self.jumpZ > 0.1
    
    def neutral(self):
        self.MAX_SPEED= 15
    
    def sprint(self):
        self.MAX_SPEED = 25
    
    def slowDown(self):
        self.MAX_SPEED = 5
    
    def jump(self):
        if not self.isJumping():
            self.jumpingSequence.start()
    
    def getLost(self):
        # for some reasons the interval doesn't set the value to zero but
        # to something close
        targetPos = self.nodepath.getPos() + self.speedVec * \
                                            self.FALLING_SPEED
        targetPos.setZ(targetPos.getZ() - self.FALLING_Z)
        fallDown = LerpPosInterval(self.nodepath, 1.0, 
                                   pos=targetPos,
                                   blendType = 'easeIn')
       # TODO send event
    
    def accelerate(self):
        if self.speed < self.MAX_SPEED:
                self.speed += .2
        else:
            self.speed = self.MAX_SPEED
    
    def decelerate(self):
        if self.speed > 0:
            self.speed -= .1
    
    def brake(self):
        if self.speed > 0:
            self.speed -= .5
            
    
# Property schema: defines the existing properties and their type
property_schema = {
                 "archetype": str,
                 "prettyName": str,
                 "python": 
                    {
                     "clazz": object
                     },
                 "position":
                    { 
                     "x": float,
                     "y": float,
                     "z": float,
                     "rotation": Types.tuple4
                     },
                 "physics": 
                    {
                     "collisionBitMask": int, # unsigned
                     "categoryBitMask" : int, # unsigned
                     "geomType": Types.Geom,
                     "geom": OdeGeom,
                     "radius": Types.float2,
                     "hasBody": bool,
                     "speed": int,
                     "density":int,
                     "xForce" : Types.float1,
                     "yForce" : Types.float1,
                     "zForce" : Types.float1,
                     "torque" : Types.float1,
                     "length": Types.float2,
                     "width": Types.float2,
                     "height": Types.float2,
                     },
                 "render": 
                    {
                     "entityType": int, # EntityType constant
                     "color": Types.Color,
                     "nodepath": NodePath,
                     "scale": int,
                     "modelPath": str,
                     "parentNode": NodePath,
                     "isDirty": bool,
                     "tags": {}
                     }
                }

dummy_template_params = {
                       "archetype": "General",
                       "prettyName": "Dummy",
                         "render": 
                        {
                         "entityType": EntityType.NONE,
                         }
                        }

entity_template_params = {
                       "archetype": "General",
                       "prettyName": "Entity",
                       "position": 
                            { 
                             "x": 0,
                             "y": 0,
                             "z": 0,
                             "rotation": (1,0,0,0)
                             },
                        "physics": 
                                {
                                 "collisionBitMask": 0x00000001,
                                 "categoryBitMask" : 0x00000000,
                                 "geomType": Types.Geom.SPHERE_GEOM_TYPE,
                                 "radius": 1,
                                 "hasBody": False
                                 },
                           "render": 
                                {
                                 "entityType": EntityType.ACTOR,
                                 "scale": 1,
                                 "modelPath": "",
                                 "isDirty": True,
                                 "color": None,
                                 "tags" : {"pos":None}
                                 }
                           }
player_params = {
                   "archetype": "Player",
                   "prettyName": "Player",
                     "render": 
                    {
                     "entityType": EntityType.NONE,
                     }
                 }                       
ball_params = {
                   "archetype": "Model",
                   "prettyName": "Ball",
                   "python":
                   {
                    "clazz": Ball
                    },
                   "physics": 
                    {
                     "collisionBitMask": 0x00000002,
                     "categoryBitMask" : 0x00000001,
                     "geomType": Types.Geom.SPHERE_GEOM_TYPE,
                     "radius":  0.13,
                     "hasBody": True,
                     "speed": 0,
                     "density":400,
                     "xForce" : 0,
                     "yForce" : 0,
                     "zForce" : 0,
                     "torque" : 0
                    },
                   "position":
                    {
                     "x": 12,
                     "y": 7,
                     "z": 0.13,
                     "rotation": (1,0,0,0)
                     },
                     "render": 
                    {
                     "isDirty": True,
                     "modelPath": "ball",
                     "scale":.3,
                     "entityType": EntityType.PLAYER
                     }
                    }

new_track_params = {
                "archetype": "Tracks",
                "prettyName": "Track",
                "position":
                    {
                     "x": 0,
                     "y": 0,
                     "z": 0,
                     "rotation": (1,0,0,0)
                     },
                "python": 
                    {
                     "clazz": Track
                     },
                "render": #necessary even if empty in order to create a NodePath
                    {
                     "entityType": EntityType.STATIC,
                     "modelPath": "track2",
                     "isDirty": True,
                     "scale": 1,
                     },
                "physics": 
                    {
                     "collisionBitMask": 0x00000001,
                     "categoryBitMask" : 0x00000002,
                     "geomType": Types.Geom.TRIMESH_GEOM_TYPE,
                     "length": 1,
                     "width": 1,
                     "height": .1,
                     "hasBody": False
                     }
                    }

environment_params = {
                      "archetype": "Background",
                      "prettyName": "Environment",
                      "position":
                            {
                             "x": -10,
                             "y": 35,
                             "z": -5,
                             "rotation": (0,0,0,0)
                             },
                      "render": 
                            {
                             "entityType": EntityType.BACKGROUND,
                             "scale": 0.25,
                             "modelPath": "environment",
                             "isDirty": True,
                             }
                        }

# create a global KeyValueObject to simplify the getPropertyType function 
schema_kvo = transformToKeyValue(property_schema)

def getPropertyType(propPath, schema=property_schema):
    if propPath is not None:
        expression = "schema_kvo.%s" % propPath
        return eval(expression)

def getPropertyPath(propName, schema=property_schema, result=""):
    """ Returns the type of a property given its name (the name is unique) """
    for key, value in schema.items():
        if key == propName:
            result += propName
            return result
        elif type(value) is dict:
            s = getPropertyPath(propName, value)
            if s is not None:
                result+= "%s.%s" % (key,s)
                return result
