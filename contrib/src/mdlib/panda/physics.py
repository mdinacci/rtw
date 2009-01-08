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
from pandac.PandaModules import Quat

from mdlib.panda import pandaCallback, SafeDirectObject
from mdlib.panda import event
from mdlib.panda import math


BOX_GEOM_TYPE = 0x1
SPHERE_GEOM_TYPE = 0x2

class PhysicManager(object):
    """ 
    PhysicManager uses the ODE library to realistically 
    simulate the game world.
    """
    # refresh rate
    REFRESH_RATE = 1/30.0
    
    # Create an accumulator to track the time since the sim has been running
    deltaTimeAccumulator = 0.0
    
    def __init__(self):
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -5.81)
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
        actor.geom.disable()
 
    def enableActor(self, actor):
        logger.debug("Enabling physic for actor %s" % actor)
        actor.geom.enable()
 
    def removeGeometryTo(self, obj):
        logger.debug("Removing geometry to %s" % obj)
        self.space.remove(obj.geom)
 
    def createGeomForActor(self, actor):
        """ Create a physical body and geometry for a game actor """
        body = OdeBody(self.physWorld)
        M = OdeMass()

        geometry = None
        geomType = actor.geomType
        if geomType == SPHERE_GEOM_TYPE:
            logger.debug("Creating a sphere geometry with radius %s for \
                actor: %s" % (actor.radius, actor.ID))
            #geometry = EntitySphereGeom(self.space, actor.radius, actor.ID)
            geometry = OdeSphereGeom(self.space, actor.radius)
            M.setSphere(actor.density, actor.radius)
            geometry.setPosition(actor.position)
        elif geomType == BOX_GEOM_TYPE:
            logger.debug("Creating sphere geom of size %s-%s-%s for actor: %s"\
                          % (actor.length, actor.width, 
                               actor.height, actor.ID))
            #geometry = EntityBoxGeom(self.space, actor.length, actor.width, actor.height, actor.ID)
            geometry = OdeBoxGeom(self.space, actor.length, actor.width, actor.height)
            M.setBox(actor.density, actor.length, actor.width, actor.height)
            pos = actor.position
            geometry.setPosition(pos.getX(), pos.getY(), pos.getZ())
        else:
            logger.error("Invalid geometry type for actor: %s" % actor)
            return None
        
        geometry.setQuaternion(math.vec4ToQuat(actor.rotation))
        geometry.setCollideBits(actor.collisionBitMask)
        geometry.setCategoryBits(actor.categoryBitMask)

        if actor.hasBody:
            logger.debug("Adding body to actor %s" % actor)
            geometry.setBody(body)
            body.setPosition(actor.position)
            body.setQuaternion(actor.rotation)
            body.setMass(M)
        
        return geometry

    def update(self, actors):
        """
        Run the physical simulation and update the actors with their
        new positions.
        """
        # Add the deltaTime for the task to the accumulator
        self.deltaTimeAccumulator += globalClock.getDt()
        while self.deltaTimeAccumulator > self.REFRESH_RATE:
            self.space.autoCollide()
            # Remove a stepSize from the accumulator until
            # the accumulated time is less than the stepsize
            self.deltaTimeAccumulator -= self.REFRESH_RATE
            # Step the simulation
            self.physWorld.quickStep(self.REFRESH_RATE)
            
            # set the new positions
            for actor in actors:
                actor.update()
    
            self.contactgroup.empty()
