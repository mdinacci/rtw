# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("physics", DEBUG)

from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdeSphereGeom, BitMask32
from pandac.PandaModules import Quat, Point3

from direct.task.TaskManagerGlobal import taskMgr
from direct.task.Task import Task

from mdlib.panda.input import SafeDirectObject
from mdlib.panda import event
from mdlib.panda import math_utils as math
from mdlib.patterns import singleton

BOX_GEOM_TYPE = 0x1
SPHERE_GEOM_TYPE = 0x2


__all__ = ["POM"]


class PhysicManager(object):
    """ 
    PhysicManager uses the ODE library to realistically 
    simulate the game world.
    """
    # refresh rate
    REFRESH_RATE = 1/40.0
    
    # Create an accumulator to track the time since the sim has been running
    deltaTimeAccumulator = 0.0
    
    def __init__(self):
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -4.81)
        self.physWorld.initSurfaceTable(1)
        # surfID1, surfID2, friction coeff, bouncy, bounce_vel, erp, cfm, slip, dampen (oscillation reduction) 
        self.physWorld.setSurfaceEntry(0, 0, 150, 0.3, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        #self.space = EntitySpace()
        self.space = OdeSimpleSpace()
        self.space.setAutoCollideWorld(self.physWorld)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
    
    def disableActor(self, actor):
        logger.debug("Disabling physic for actor %s" % actor)
        actor.physics.geom.disable()
 
    def enableActor(self, actor):
        logger.debug("Enabling physic for actor %s" % actor)
        actor.physics.geom.enable()
 
    def addGeomToSpace(self, geom):
        self.space.add(geom)
 
    def removeGeometryTo(self, obj):
        logger.debug("Removing geometry to %s" % obj)
        geom = obj.physics.geom
        self.space.remove(geom)
        del obj.physics.geom
 
    def createGeomForObject(self, object, position):
        """ Create a physical body and geometry for a game object """
        M = OdeMass()
        geometry = None
        geomType = object.geomType
        if geomType == SPHERE_GEOM_TYPE:
            logger.debug("Creating a sphere geometry with radius %s for \
                object: %s" % (object.radius, object))
            geometry = OdeSphereGeom(self.space, object.radius)
            geometry.setPosition(position.x, position.y, position.z)
            
            if object.hasBody:
                M.setSphere(object.density, object.radius)
        
        elif geomType == BOX_GEOM_TYPE:
            logger.debug("Creating sphere geom of size %s-%s-%s for object: %s"\
                          % (object.length, object.width, 
                               object.height, object))
            geometry = OdeBoxGeom(self.space, object.length, object.width, object.height)
            l, w, h = (object.length, object.width, object.height)
            geometry.setPosition(position.x, position.y, position.z)
            
            if object.hasBody:
                M.setBox(object.density, object.length, object.width, object.height)
                #M.setBox(object.density, object.length, object.width, object.height)
        else:
            logger.error("Invalid geometry type for object: %s" % object)
            return None
        
        #geometry.setPosition(position.x, position.y, position.z)
        geometry.setQuaternion(math.vec4ToQuat(position.rotation))
        geometry.setCollideBits(object.collisionBitMask)
        geometry.setCategoryBits(object.categoryBitMask)

        if object.hasBody:
            logger.debug("Adding body to object %s" % object)
            body = OdeBody(self.physWorld)
            
            # FIXME !!! object change position to 0,0,0
            oldPos = geometry.getPosition()
            oldRot = geometry.getQuaternion()
            geometry.setBody(body)
            # reset them as they are "deleted" by the previous line
            geometry.setPosition(oldPos)
            geometry.setQuaternion(oldRot)
            #geometry.setPosition(position.x, position.y, position.z)
            #geometry.setQuaternion(math.vec4ToQuat(position.rotation))
            
            body.setPosition(geometry.getPosition())
            body.setQuaternion(geometry.getQuaternion())
            body.setMass(M)
        
        return geometry
    
    def update(self, scene):
        """
        Run the physical simulation and update the actors with their
        new positions.
        """
        
        actors = scene.getDirtyActors()
        
        # apply forces if necessary
        for actor in actors:
            phys = actor.physics
            if phys.has_key("xForce") and phys.xForce != 999:
                xf,yf,zf = (phys.xForce, phys.yForce, phys.zForce)
                logger.debug("Applying force %d-%d-%d to actor %s" % \
                             (xf,yf,zf,actor.UID))
                body = phys.geom.getBody()
                speed = phys.linearSpeed
                body.addForce(xf*speed, yf*speed, zf*speed)
                phys.xForce = 999
                
        # collision step
        if len(actors) > 0:
            self.deltaTimeAccumulator += globalClock.getDt()
            while self.deltaTimeAccumulator > self.REFRESH_RATE:
                self.space.autoCollide()
                self.deltaTimeAccumulator -= self.REFRESH_RATE
                self.physWorld.quickStep(self.REFRESH_RATE)
                
                for actor in actors:
                    if actor.has_key("physics") and actor.physics.has_key("geom"):
                        pos = actor.physics.geom.getPosition()
                        actor.position.x = pos[0]
                        actor.position.y = pos[1]
                        actor.position.z = pos[2]
                        actor.position.rotation = actor.physics.geom.getQuaternion()
                        
                self.contactgroup.empty()

POM = PhysicManager()
