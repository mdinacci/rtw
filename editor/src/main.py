# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
License: BSD

World Editor for SpeedBlazer
"""

from mdlib.decorator import traceMethod, accepts, trace, dumpArgs
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("editor", DEBUG)

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "show-frame-rate-meter 1")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import Point3, Vec4, Vec3, NodePath, Quat
from pandac.PandaModules import LightAttrib, AmbientLight, DirectionalLight
from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, CollisionTraverser, CollisionRay, GeomNode
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdeSphereGeom, BitMask32

from sys import exit 

# to randomly choose a color
from random import randint, seed
seed()

from mdlib.panda import loadModel, pandaCallback, SafeDirectObject
from mdlib.panda.camera import *

# some colors
BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
RED = Vec4(1,0,0,1)
GREEN = Vec4(0,1,0,1)
BLUE = Vec4(0,0,1,1)
HIGHLIGHT = Vec4(1,1,0.3,0.5)
colors = [BLACK,WHITE,RED,GREEN,BLUE]

# All the objects are attached to the master node
masterNode = render.attachNewNode("master")

class GameEntity(object):
    """ 
    Basic entity of the game 
    TODO: pos, quat and density must be properties
    """
    def __init__(self, path, parent, scale, pos):
        self._nodePath = loadModel(loader, path, parent, scale, pos)
        self._nodePath.showTightBounds()

    def __repr__(self):
        return self.__class__.__name__
        
    def getNodePath(self):
        return self._nodePath
       
    def getPos(self):
        return self._nodePath.getPos()
    
    def getQuat(self):
        return self._nodePath.getQuat()
    
    
class GameActor(GameEntity):
    """  
    A game actor is different from a GameEntity in the sense that
    it can physically interact with the world.
    It is usually represented by a 3D model and has physical properties. 
    """
    
    BOX_GEOM_TYPE = "box"
    SPHERE_GEOM_TYPE = "sphere"
    
    def __init__(self, path, parent, scale, pos):
        super(GameActor, self).__init__(path, parent, scale, pos)
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
    LENGTH = 2
    HEIGHT = .2

    def __init__(self, parent, pos):
        super(Cell, self).__init__("../res/cell", parent, 1, pos)
        self.getNodePath().setColor(colors[randint(0,len(colors)-1)])
        self._setupPhysics()
     
    def hasBody(self):
        return False
     
    def getBody(self):
        return None
        
    def _setupPhysics(self): 
        self._density = 400
        self._collisionBitMask = BitMask32.bit(1)#(0x00000001)
        self._categoryBitMask = BitMask32.allOff()#(0x00000001) #2
        self._geomType = GameActor.BOX_GEOM_TYPE 
        
class Track(GameEntity):
    _cells = []
    ROW_LENGTH = 5
    
    def __init__(self):
        self._nodePath = masterNode.attachNewNode("track")
    
    def getCellAtIndex(self, idx):
        if idx < len(self._cells):
            return self._cells[idx]
        else:
            logger.error("Cell %d doesn't exists !" % idx)
    
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
                incX = - (self.ROW_LENGTH-1) * Cell.LENGTH
                incY = Cell.LENGTH
            else:
                incX = Cell.LENGTH
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
    RADIUS = 1
    
    _isMoving = False
    
    def __init__(self, parent, pos):
        super(TheBall, self).__init__("models/smiley", parent, 1, pos)
        self._setupPhysics()
        
    def _setupPhysics(self): 
        self._density = 100
        self._collisionBitMask = BitMask32.allOff()#(0x00000002) #2
        self._categoryBitMask = BitMask32.bit(1)#(0x00000001)
        self._geomType = GameActor.SPHERE_GEOM_TYPE
    
    
class PhysicSimulation(object):
    # Create an accumulator to track the time since the sim has been running
    deltaTimeAccumulator = 0.0
    
    def __init__(self, visualWorld):
        self.visualWorld = visualWorld
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -5.81)
        #self.physWorld.setGravity(0, 0, 0)
        self.physWorld.initSurfaceTable(1)
        # surfID1, surfID2, friction coeff, bouncy, bounce_vel, erp, cfm, slip, dampen (oscillation reduction) 
        self.physWorld.setSurfaceEntry(0, 0, 150, 1.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.space = OdeSimpleSpace()
        self.space.setAutoCollideWorld(self.physWorld)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
 
        taskMgr.doMethodLater(0.5, self._simulationTask, "Physics Simulation")
 
    @dumpArgs
    def createBodyForEntity(self, entity):
        """ Create a physical body and geometry for a game entity (actor) """
        
        body = OdeBody(self.physWorld)
        M = OdeMass()

        geometry = None
        geomType = entity.getGeometryType()
        if geomType == GameActor.SPHERE_GEOM_TYPE:
            geometry = OdeSphereGeom(self.space, 1)
            M.setSphere(entity.getDensity(), 1)
        elif geomType == GameActor.BOX_GEOM_TYPE:
            geometry = OdeBoxGeom(self.space, 1, 1, 0.2)
            M.setBox(entity.getDensity(), 1, 1, 0.2)
        else:
            logger.error("Invalid geometry type for entity: %s" % entity)
            return None
        
        geometry.setPosition(entity.getPos())
        geometry.setQuaternion(entity.getQuat())
        
        geometry.setCollideBits(entity.getCollisionBitMask())
        geometry.setCategoryBits(entity.getCategoryBitMask())

        if entity.hasBody():
            geometry.setBody(body)
    
            body.setMass(M)
            body.setPosition(entity.getPos())
            body.setQuaternion(entity.getQuat())
    
        return body
    
    @pandaCallback
    def _simulationTask(self, task):
        # Add the deltaTime for the task to the accumulator
        self.deltaTimeAccumulator += globalClock.getDt()
        while self.deltaTimeAccumulator > Editor.FPS:
            self.space.autoCollide()
            # Remove a stepSize from the accumulator until
            # the accumulated time is less than the stepsize
            self.deltaTimeAccumulator -= Editor.FPS
            # Step the simulation
            self.physWorld.quickStep(Editor.FPS)
            
        # set the new positions
        actors = self.visualWorld.getActors()
        for actor in actors:
            if actor.hasBody():
                body = actor.getBody()
                actor.update(body.getPosition(), Quat(body.getQuaternion()))
            
        self.contactgroup.empty()
        
        return task.cont
 
class World(object):
    """
    The world contains and manage (by delegating) everything is in the 3D world
    """
    def __init__(self):
        # setup the environment and the lights
        self._prepareWorld()
        
        self._entities = []
        self._track = Track()
        self.addEntity(self._track)
        
        self.physWorld = PhysicSimulation(self)
        
    def addEntity(self, entity):
        self._entities.append(entity)
        if isinstance(entity, GameActor):
            # TODO should be splitted in createGeometry and setBody, and the latter
            # must be called only if entity.hasBody returns True !!
            entity.setBody(self.physWorld.createBodyForEntity(entity))
        logger.debug("Added new entity in the world %s" % entity)
        
    def getTrack(self):
        return self._track
    
    def getActors(self):
        # TODO this loop can be computed only if we add a new entity
        # evaluate time/space 
        actors = []
        for entity in self._entities:
            if isinstance(entity, GameActor):
                actors.append(entity)
                
        return actors
    
    def _setupLights(self):
        #Create some lights and add them to the scene. By setting the lights on
        #render they affect the entire scene
        #Check out the lighting tutorial for more information on lights
        lAttrib = LightAttrib.makeAllOff()
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(.4, .4, .35, 1) )
        lAttrib = lAttrib.addLight( ambientLight )
        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setDirection( Vec3( 0, 8, -2.5 ) )
        directionalLight.setColor( Vec4( 0.9, 0.8, 0.9, 1 ) )
        lAttrib = lAttrib.addLight( directionalLight )
        render.attachNewNode( directionalLight.upcastToPandaNode() )
        render.attachNewNode( ambientLight.upcastToPandaNode() )
        render.node().setAttrib( lAttrib )
        
    def _prepareWorld(self):
        env = GameEntity("../res/environment", masterNode, 0.25, Point3(-8,42,-5))
        #self._entities.append(env)    
        self._setupLights()
        
class EditorMode(object):
    def __init__(self, world):
        self.world = world
        self._setupInput()
        self._setupCamera()
        self._setupCollisionDetection()
    
    def enable(self):
        self.camera.enable()
        
    def disable(self):
        self.camera.disable()
        self.input.ignoreAll()       
        
    def _setupCamera(self):
        raise NotImplementedError
    
    def _setupInput(self):
        raise NotImplementedError
    
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("cellPickRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
class RoamMode(EditorMode):
    def __init__(self, world):
        super(RoamMode, self).__init__(world)
    
    def _setupCamera(self):
        self.camera = RoamingCamera(setActive = False)
        self.camera.setPos(0,-40,13)
        self.camera.lookAt(0,0,0)
    
    def _setupInput(self):
        self.input = DirectObject()

class DriveMode(EditorMode):
    """ This mode is used to simulate the game """
    def __init__(self, world):
        super(DriveMode, self).__init__(world)
        self._setupCollisionDetection()

class EditMode(EditorMode):
    class PickedObjectState(object):
        color = BLACK = Vec4(0,0,0,1)
        index = -1
    
    def __init__(self, world):
        super(EditMode, self).__init__(world)
        self._setupCollisionDetection()
        self.disable()
        
    def enable(self):
        super(EditMode, self).enable()
        self.__setupInput()
    
    def __hasSelection(self):
        return hasattr(self, "pickedObjectState")
    
    @pandaCallback
    def _addRow(self):
        self.world.getTrack().addRow()
        
    @pandaCallback
    def _addCell(self):
        self.world.getTrack().addCell()
        
    @pandaCallback
    def _addBall(self):
        # FIXME get position from mouse pointer,
        # cast a ray to the track and the intersection point
        # is the spawning position.
        ball = TheBall(masterNode, Point3(4,2,10))
        messenger.send("entity-new", [ball])
    
    @pandaCallback
    def _onMousePress(self):
        track = self.world.getTrack()
        trackNP = track.getNodePath()
        if base.mouseWatcherNode.hasMouse():
            mousePos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mousePos.getX(), mousePos.getY())
            self.picker.traverse(trackNP)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                
                if self.__hasSelection():
                    previousIndex = self.pickedObjectState.index
                    #previousColor = self.pickedObjectState.color
                    cell = track.getCellAtIndex(previousIndex).getNodePath()
                    #cell.setColor(previousColor)
                    cell.hideBounds()
                    cell.setRenderModeFilled()
                else:
                    self.pickedObjectState = self.PickedObjectState()
                    
                pickedObject = self.pq.getEntry(0).getIntoNodePath()
                row, col = map(lambda x: int(x), pickedObject.getNetTag("pos").split())
                idx = row*Track.ROW_LENGTH+col
                logger.debug("Selected object: %s at row,col: %d,%d (idx: %d)" % (pickedObject, row, col, idx ))
                
                currentCell = track.getCellAtIndex(idx).getNodePath()
                self.pickedObjectState.color = currentCell.getColor()
                self.pickedObjectState.index = idx
                
                #currentCell.setColor(HIGHLIGHT)
                currentCell.showBounds()
                currentCell.setRenderModeWireframe()
            else:
                logger.debug("No collisions at: %s" % mousePos)
    
    def _setupCamera(self):
        self.camera = FixedCamera(setActive = False)
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)

    def _setupInput(self):
        self.input = DirectObject()
        self.__setupInput()

    def __setupInput(self):
        self.input.accept("space", self._addCell)
        self.input.accept("shift-space", self._addRow)
        self.input.accept("mouse1", self._onMousePress)
        self.input.accept("entity-new", self.world.addEntity)
        self.input.accept("b", self._addBall)
        
class Editor(object):
    FPS = 1.0/80.0
    
    def __init__(self):
        self.world = World()

        self.ins = DirectObject()
        self._attachControls()
        
        self.modes = {"roam": RoamMode(self.world), 
                      "edit": EditMode(self.world)}
        self.mode = self.modes["roam"]
        self.mode.enable()
        
        self.isRunning = True
        
        if False:
            taskMgr.popupControls()
            messenger.toggleVerbose()
    
    def _attachControls(self):
        self.ins.accept("escape", self.quit)
        self.ins.accept("1", self._switchMode, ["roam"])
        self.ins.accept("2", self._switchMode, ["edit"])
        
    @pandaCallback
    def _switchMode(self, mode):
        if mode in self.modes.keys():
            if self.mode != self.modes[mode]:
                logger.info("switching to %s mode" % mode)
                self.mode.disable()
                self.mode = self.modes[mode]
                self.mode.enable()
        else:
            logger.error("Mode %s doesn't exists" % mode)
    
    def quit(self):
        self.isRunning = False
    
    def run(self):
        from time import sleep
        while self.isRunning:
            sleep(self.FPS)
            taskMgr.step()
        else:
            render.analyze()
            # TODO do cleanup
            logger.info("Quitting application, have fun")

if __name__ == "__main__":
    e = Editor()
    e.run()
    