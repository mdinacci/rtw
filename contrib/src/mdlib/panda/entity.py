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

from direct.interval.LerpInterval import LerpFuncNS, LerpPosInterval, LerpScaleInterval
from direct.interval.IntervalGlobal import Sequence
from direct.interval.FunctionInterval import Wait, Func
from direct.interval.MetaInterval import Parallel
from direct.showbase.PythonUtil import Functor

from pandac.PandaModules import NodePath, Point3, OdeGeom, Quat, Material, Vec4
from pandac.PandaModules import AntialiasAttrib


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
        self._segments = []
        self.currentSegmentNum = 0
        
    def unfold(self):
        def sortBySegmentNumber(x,y):
            nameX = x.getName()
            nameY = y.getName()
            numX = int(nameX[nameX.index("@")+1:])
            numY = int(nameY[nameY.index("@")+1:])
            
            if numX > numY: return 1
            elif numX < numY: return -1
            else: return 0
            
        self.render.nodepath.setTwoSided(False)
        
        # XXX
        # flattening is fundamental, I don't know why but otherwise the 
        # track is not scaled, so it looks much bigger :O
        self.render.nodepath.flattenMedium()

        # create a copy of the track that will be shown to the player
        # only the tiles are copied
        self.trackCopy = NodePath("trackCopy")
        self.render.nodepath.find("**/tiles").copyTo(self.trackCopy)
        self.trackCopy.reparentTo(render)
        
        # flatten all tiles but keep the segment intact
        self.trackCopy.flattenStrong()
        self.trackCopy.show()
        #self.trackCopy.setAntialias(AntialiasAttrib.MLine)
        
        # this will be used for checkpoints
        n = self.render.nodepath
        rows = n.findAllMatches("**/straight*").asList()
        curves = n.findAllMatches("**/curve*").asList()
        segments = rows + curves
        segments.sort(cmp=sortBySegmentNumber)
        self._segments = segments
        
        
        # hide the tiles but not the other items
        self.render.nodepath.find("**/tiles").hide()
        
    
    # this will be used for checkpoints
    def setCurrentTile(self, tile):
        segment = tile.getParent().getParent()
        name = segment.getName()
        self.currentSegmentNum = int(name[name.index("@")+1:])
        
        if segment.getTag("endpoint") == "1":
            messenger.send(event.END_TRACK)
    
    def serialise(self):
        attrs = super(Track, self).serialise()
        del attrs._tiles
        return attrs

    segments = property(fget=lambda self: self._segments)
    

class Ball(GameEntity):
    #maxSpeed = 30
    FALLING_SPEED = 250
    FALLING_Z = 5
    
    def __init__(self, uid, data):
        super(Ball, self).__init__(uid, data)
        self.frozen = False
        self.specialItem = None
        
        jumpUp = LerpFuncNS(Functor(self.__setattr__,"jumpZ"), 
                    blendType="easeOut",duration=.2, 
                    fromData=self.physics.jumpZ, toData=self.physics.jumpHeight)
        jumpDown = LerpFuncNS(Functor(self.__setattr__,"jumpZ"), 
                      blendType="easeIn",duration=.2, 
                      fromData=self.physics.jumpHeight, toData=0)
        self.jumpingSequence = Sequence(jumpUp, jumpDown, name="jumping")
        
        self.originalMaxSpeed = self.physics.maxSpeed
    
    def setSpecialItem(self, item):
        self.specialItem = item
    
    def hasSpecialItem(self):
        return self.specialItem is not None
    
    def setBall(self, ball):
        self.ball = ball
        self.ball.nodepath.setPos(self.nodepath.getPos())
    
    def update(self):
        pass
    
    def turnRight(self):
        currentH = self.nodepath.getH()
        self.nodepath.setH(currentH - self.physics.steeringFactor)
    
    def turnLeft(self):
        currentH = self.nodepath.getH()
        self.nodepath.setH(currentH + self.physics.steeringFactor)
    
    def isJumping(self):
        return self.physics.jumpZ > 0.1
    
    def neutral(self):
        self.physics.maxSpeed= self.originalMaxSpeed
    
    def minimize(self):
        originalScale = self.render.scale
        scaleDown = LerpScaleInterval(self.nodepath, .5, .3, 
                                      originalScale)
        
        scaleUp = LerpScaleInterval(self.nodepath, .5, originalScale, 
                                      .3)
        
        originalMaxSpeed = self.physics.maxSpeed
        newSpeed = self.physics.maxSpeed / 3.0 * 2
        slowDown = LerpFuncNS(Functor(self.__setattr__,"maxSpeed"), 
                    blendType="easeOut",duration=.5, 
                    fromData=originalMaxSpeed, toData=newSpeed)
        fastenUp = LerpFuncNS(Functor(self.__setattr__,"maxSpeed"), 
                      blendType="easeIn",duration=.5, 
                      fromData=newSpeed, toData=originalMaxSpeed)
        Sequence(Parallel(scaleDown, slowDown), Wait(3), 
                 Parallel(scaleUp, fastenUp)).start()

    
    def sprint(self):
        return
        if not self.isJumping():
            self.physics.maxSpeed = 40
            self.physics.speed *= 2
            if self.physics.speed == 0:
                self.physics.speed = self.physics.maxSpeed / 2
            if self.physics.speed > self.physics.maxSpeed:
                self.physics.speed = self.physics.maxSpeed
    
    def slowDown(self):
        if not self.isJumping():
            self.physics.maxSpeed = 10
            self.physics.speed /= 2
            if self.physics.speed < self.physics.maxSpeed:
                self.physics.speed = self.physics.maxSpeed

    def freeze(self):
        if self.frozen == False:
            if not self.isJumping():
                self.frozen = True
                self.physics.speed = 0
                delay = Wait(2)
                Sequence(delay, Func(self.__setattr__, "frozen", False)).start()
        else:
            self.speed = 0
    
    def invisibleMode(self):
        delay = Wait(3)
        Sequence(Func(self.nodepath.hide), delay, 
                 Func(self.nodepath.show)).start()
    
    def jump(self):
        if not self.isJumping():
            self.jumpingSequence.start()
    
    def getLost(self):
        # for some reasons the interval doesn't set the value to zero but
        # to something close
        targetPos = self.nodepath.getPos() + self.physics.speedVec * \
                                            self.FALLING_SPEED
        targetPos.setZ(targetPos.getZ() - self.FALLING_Z)
        fallDown = LerpPosInterval(self.nodepath, 15.0/self.physics.speed, 
                                   pos=targetPos,
                                   blendType = 'easeIn')
        fallDown.start()
       # TODO send event
    
    def accelerate(self):
        if not self.frozen:
            if self.physics.speed < self.physics.maxSpeed:
                self.physics.speed += .2
            else:
                self.physics.speed = self.physics.maxSpeed
    
    def decelerate(self):
        if self.physics.speed > 0:
            self.physics.speed -= .1
    
    def brake(self):
        if self.physics.speed > 0:
            self.physics.speed -= .5
            


    
# Property schema: defines the existing properties and their type
property_schema = {
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
                 "ode": 
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

player_params = {
                   "prettyName": "Player",
                     "render": 
                    {
                     "entityType": EntityType.NONE,
                     }
                 }       
                
shark_ball_params = {
                   "prettyName": "Shark",
                   "python":
                   {
                    "clazz": Ball
                    },
                    "props": 
                    {
                     "speed":70,
                     "control":40,
                     "jump":40,
                     "acceleration":70,
                    },
                    "physics":
                    {
                     "radius":  0.4,
                     "maxSpeed": 42,
                     "steeringFactor" : .5,
                     "spinningFactor" : 80,
                     "jumpHeight" : .6,
                     "speed" : 0,
                     "jumpZ" : 0
                     },
                   "position":
                    {
                     "x": 6,
                     "y": 0,
                     "z": 0,
                     "rotation": (1,0,0,0)
                     },
                     "render": 
                    {
                     "isDirty": True,
                     "modelPath": "ball",
                     "scale":1,
                     "entityType": EntityType.PLAYER
                     }
                    }

photon_ball_params = {
                   "prettyName": "Photon",
                   "python":
                   {
                    "clazz": Ball
                    },
                    "props": 
                    {
                     "speed":80,
                     "control":70,
                     "jump":60,
                     "acceleration":80,
                    },
                    "physics":
                    {
                     "radius":  0.4,
                     "maxSpeed": 50,
                     "steeringFactor" : .4,
                     "spinningFactor" : 80,
                     "jumpHeight" : .6,
                     "speed" : 0,
                     "jumpZ" : 0
                     },
                   "position":
                    {
                     "x": 6,
                     "y": 0,
                     "z": 0,
                     "rotation": (1,0,0,0)
                     },
                     "render": 
                    {
                     "isDirty": True,
                     "modelPath": "ball",
                     "scale":1,
                     "entityType": EntityType.PLAYER
                     }
        }

avg_joe_ball_params = {
                   "prettyName": "Average Joe",
                   "python":
                   {
                    "clazz": Ball
                    },
                    "props": 
                    {
                     "speed":50,
                     "control":70,
                     "jump":60,
                     "acceleration":60,
                    },
                    "physics":
                    {
                     "radius":  0.4,
                     "maxSpeed": 32,
                     "steeringFactor" : .6,
                     "spinningFactor" : 80,
                     "jumpHeight" : .6,
                     "speed" : 0,
                     "jumpZ" : 0
                     },
                   "position":
                    {
                     "x": 6,
                     "y": 0,
                     "z": 0,
                     "rotation": (1,0,0,0)
                     },
                     "render": 
                    {
                     "isDirty": True,
                     "modelPath": "ball",
                     "scale":1,
                     "entityType": EntityType.PLAYER
                     }
        }

turtle_king_ball_params = {
                   "prettyName": "Turtle King",
                   "python":
                   {
                    "clazz": Ball
                    },
                    "props": 
                    {
                     "speed":30,
                     "control":70,
                     "jump":60,
                     "acceleration":30,
                    },
                    "physics":
                    {
                     "radius":  0.4,
                     "maxSpeed": 25,
                     "steeringFactor" : .7,
                     "spinningFactor" : 80,
                     "jumpHeight" : .6,
                     "speed" : 0,
                     "jumpZ" : 0
                     },
                   "position":
                    {
                     "x": 6,
                     "y": 0,
                     "z": 0,
                     "rotation": (1,0,0,0)
                     },
                     "render": 
                    {
                     "isDirty": True,
                     "modelPath": "ball",
                     "scale":1,
                     "entityType": EntityType.PLAYER
                     }
        }


new_track_params = {
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
                     "modelPath": "track.bam",
                     "isDirty": True,
                     "scale": .4,
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
                      "prettyName": "Environment",
                      "position":
                            {
                             "x": 0,
                             "y": 0,
                             "z": -30,
                             "rotation": (0,0,0,0)
                             },
                      "render": 
                            {
                             "entityType": EntityType.BACKGROUND,
                             "scale": 200,
                             "modelPath": "env",
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
