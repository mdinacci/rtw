# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
License: BSD

World Editor for SpeedBlazer


TODO

- delete cell (send event)
- change cell specific settings:
    - model
    - color
    - surface properties
- create multiple surfaces in ODE and bind them to cells
- implement scene save/load
- better ball physics (fix the fact that it never stops)
- entity manager
- input manager, the situation is getting out of control, who binds which key?
- better camera for the ball, must have constant X position and 
  constant Y distance
- new cell models to implement elevation
- curves :O
- fix the logger
- improve button location, now depends on the window' size
- Configuration manager
"""

# useful for debugging
from mdlib.decorator import traceMethod, accepts, trace, dumpArgs

# logging
from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("editor", WARNING)

# load configuration
from pandac.PandaModules import loadPrcFile, ConfigVariableString, ConfigVariableBool
loadPrcFile("../res/Config.prc")
loadPrcFile("../res/Editor.prc")

# panda 3d stuff
import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import Point3, Vec4, Vec3, NodePath, Quat
from pandac.PandaModules import LightAttrib, AmbientLight, DirectionalLight

# collision to pick cell with mouse
from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, CollisionTraverser, CollisionRay, GeomNode

# ode imports
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdeSphereGeom, BitMask32

from direct.gui.DirectGui import *

from sys import exit 

# panda utilities and actors
from mdlib.panda import pandaCallback, SafeDirectObject
from mdlib.panda.camera import *
from mdlib.panda.entity import *

# All the objects are attached to the master node
masterNode = render.attachNewNode("editorNode")

    
class PhysicSimulation(object):
    # Create an accumulator to track the time since the sim has been running
    deltaTimeAccumulator = 0.0
    
    def __init__(self, visualWorld):
        self.visualWorld = visualWorld
        self.physWorld = OdeWorld()
        self.physWorld.setGravity(0, 0, -9.81)
        #self.physWorld.setGravity(0, 0, 0)
        self.physWorld.initSurfaceTable(1)
        # surfID1, surfID2, friction coeff, bouncy, bounce_vel, erp, cfm, slip, dampen (oscillation reduction) 
        #self.physWorld.setSurfaceEntry(0, 0, 150, 0.1, 1, 0.9, 0.000001, 0.0, 0.002)
        self.physWorld.setSurfaceEntry(0, 0, 150, 0.3, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.space = OdeSimpleSpace()
        self.space.setAutoCollideWorld(self.physWorld)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
 
        taskMgr.doMethodLater(0.5, self._simulationTask, "Physics Simulation")
 
    def createBodyForEntity(self, entity):
        """ Create a physical body and geometry for a game entity (actor) """
        
        body = OdeBody(self.physWorld)
        M = OdeMass()
        np = entity.getNodePath()

        geometry = None
        geomType = entity.getGeometryType()
        if geomType == GameActor.SPHERE_GEOM_TYPE:
            geometry = OdeSphereGeom(self.space, entity.radius)
            M.setSphere(entity.getDensity(), entity.radius)
            geometry.setPosition(entity.getPos())
        elif geomType == GameActor.BOX_GEOM_TYPE:
            geometry = OdeBoxGeom(self.space, entity.length, entity.width, entity.height)
            M.setBox(entity.getDensity(), entity.length, entity.width, entity.height)
            geometry.setPosition(np.getX(), np.getY(), np.getZ()-entity.height)
        else:
            logger.error("Invalid geometry type for entity: %s" % entity)
            return None
        
        geometry.setQuaternion(entity.getQuat())
        geometry.setCollideBits(entity.getCollisionBitMask())
        geometry.setCategoryBits(entity.getCategoryBitMask())

        if entity.hasBody():
            geometry.setBody(body)
            body.setPosition(entity.getPos())
            body.setQuaternion(entity.getQuat())
            body.setMass(M)
        
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
        self._entities = []
        # setup the environment and the lights
        self.physWorld = PhysicSimulation(self)
        self._prepareWorld()
        
        self._track = Track(masterNode)
        self.addEntity(self._track)
        
        self._ball = TheBall(masterNode, Point3(4,2,5))
        self.addEntity(self._ball)
        self._ball.getNodePath().hide()
        # just in case there is no track yet, otherwise the ball would fall
        # forever 
        self._ball.getBody().setGravityMode(False)
        
    def addEntity(self, entity):
        self._entities.append(entity)
        if isinstance(entity, GameActor):
            # TODO should be splitted in createGeometry and setBody, and the latter
            # must be called only if entity.hasBody returns True !!
            # FIXME shouldn't the Actor create the body itself ?
            entity.setBody(self.physWorld.createBodyForEntity(entity))
        logger.debug("Added new entity in the world %s" % entity)
        
    def getTrack(self):
        return self._track
    
    def getBall(self):
        return self._ball
    
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
        env = Environment(masterNode, Point3(-8,42,-5))
        self._entities.append(env)    
        self._setupLights()
        
class EditorMode(object):
    def __init__(self, world):
        self.world = world
        self._setupCamera()
        self._setupInput()
    
    def enable(self):
        self.camera.enable()
        self._setupInput()
        
    def disable(self):
        self.camera.disable()
        self.input.ignoreAll()       
        
    def _setupCamera(self):
        raise NotImplementedError
    
    def _setupInput(self):
        raise NotImplementedError

    
class RoamMode(EditorMode):
    def __init__(self, world):
        super(RoamMode, self).__init__(world)
    
    def _setupCamera(self):
        self.camera = RoamingCamera()
        self.camera.setPos(0,-40,10)
        self.camera.lookAt(0,0,0)
    
    def _setupInput(self):
        self.input = DirectObject()
        self.input.accept("0", self.camera.lookAtOrigin)


class DriveMode(EditorMode):
    """ This mode is used to simulate the game """
    def __init__(self, world):
        super(DriveMode, self).__init__(world)
    
    def enable(self):
        super(DriveMode, self).enable()
        self.world.getBall().getNodePath().show()
        self.world.getBall().getBody().setGravityMode(True)
    
    def disable(self):
        super(DriveMode, self).disable()
        self.world.getBall().getNodePath().hide()
        # TODO
        #self.world.getBall().stop()
    
    def _setupCamera(self):
        # 3,3,-0.5 is the perfect setup to check the collision of the ball 
        # against the track
        self.camera = TheBallCamera(self.world.getBall(), 8, 10, 6)
        
    def _setupInput(self):
        self.input = DirectObject()
        self.__setupInput()
        
    def __setupInput(self):
        ball = self.world.getBall()
        self.input.accept("i", ball._setForce, [0,1.5,0])
        self.input.accept("j", ball._setForce, [-2,0,0])
        self.input.accept("k", ball._setForce, [0,-0.5,0])
        self.input.accept("l", ball._setForce, [2,0,0])
        self.input.accept("i-up", ball._setForce, [0,0,0])
        self.input.accept("j-up", ball._setForce, [0,0,0])
        self.input.accept("k-up", ball._setForce, [0,0,0])
        self.input.accept("l-up", ball._setForce, [0,0,0])


class DebugMode(EditorMode):
    def __init__(self, world):
        super(DebugMode, self).__init__(world)
    
    def _setupCamera(self):
        self.camera = DebugCamera()
    
    def _setupInput(self):
        pass
    
    def enable(self):
        pass
        
    def disable(self):
        pass


class EditMode(EditorMode):
    class PickedObjectState(object):
        color = BLACK = Vec4(0,0,0,1)
        index = -1
    
    class GUIControllerDelegate(object):
        def __init__(self, editMode):
            # Inner classes don't have access to the outer
            # class attributes like in Java :(
            self._editMode = editMode
        
        def __getattr__(self,attr):
            try:
                return self.__dict__[attr]
            except KeyError, e:
               return self._editMode.__dict__[attr]
        
        def onDeleteButtonClick(self):
            logger.debug("sending message delete-entity")
            messenger.send("delete-entity", [self._selectedCell])
    
    def __init__(self, world):
        super(EditMode, self).__init__(world)
        self._setupCollisionDetection()
        self._selectedCell = None
        self._gui = EditModeGUI(self.GUIControllerDelegate(self))
        self.disable()
        
    def enable(self):
        super(EditMode, self).enable()
        self._gui.enable()
        
    def disable(self):
        super(EditMode, self).disable()
        self._gui.disable()
        if self._selectedCell is not None:
            self._selectedCell.getNodePath().hideBounds()
    
    def __hasSelection(self):
        return hasattr(self, "pickedObjectState")
    
    #pandaCallback
    def _deleteCell(self, cell):
        logger.debug("Deleting cell: %s", cell)
    
    @pandaCallback
    def _addRow(self):
        logger.debug("Adding row to track")
        self.world.getTrack().addRow()
        
    @pandaCallback
    def _addCell(self):
        logger.debug("Adding cell to track")
        self.world.getTrack().addCell()
        
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
                    cell = track.getCellAtIndex(previousIndex).getNodePath()
                    cell.hideBounds()
                    cell.setRenderModeFilled()
                else:
                    self.pickedObjectState = self.PickedObjectState()
                    
                pickedObject = self.pq.getEntry(0).getIntoNodePath()
                row, col = map(lambda x: int(x), pickedObject.getNetTag("pos").split())
                idx = row*Track.ROW_LENGTH+col
                logger.debug("Selected object: %s at row,col: %d,%d (idx: %d)" % (pickedObject, row, col, idx ))
                
                self._selectedCell = track.getCellAtIndex(idx)
                np = self._selectedCell.getNodePath()
                self.pickedObjectState.color = np.getColor()
                self.pickedObjectState.index = idx
                
                np.showBounds()
                #currentCell.setRenderModeWireframe()
            else:
                logger.debug("No collisions at: %s" % mousePos)
    
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("cellPickRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
    def _setupCamera(self):
        self.camera = FixedCamera()
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


class EditModeGUI(object):
    def __init__(self, controller):
        self.controller = controller
        maps = loader.loadModel('delete_btn/delete_btn.egg')
        ra = base.camLens.getAspectRatio()
        deleteBtn = DirectButton(geom = (maps.find('**/delete'),
                         maps.find('**/delete'),
                         maps.find('**/delete_over'),
                         maps.find('**/delete')),
                         borderWidth=(0,0),
                         frameColor=(0,0,0,0),
                         scale = .2,
                         pos = (-.8*ra,0,.6*ra),
                         command=self.controller.onDeleteButtonClick)
        
        deleteBtn.hide()
        self._widgets = [deleteBtn]
        
    @pandaCallback
    def _deleteButtonClick(self):
        messenger.send("delete-cell-button-click")
        
    
    def enable(self):
        for widget in self._widgets:
            widget.show()
    
    def disable(self):
        for widget in self._widgets:
            widget.hide()
    

class Editor(object):
    FPS = 1.0/90.0
    
    def __init__(self):
        self.world = World()

        self.ins = DirectObject()
        self._setupInput()
        
        # if want-directtols is true, don't activate all the modes
        if wantsDirectTools():
            self.modes = {"debug": DebugMode(self.world)}
            self.mode = self.modes["debug"]
        else:
            self.modes = {"roam": RoamMode(self.world), 
                          "edit": EditMode(self.world),
                          "drive":DriveMode(self.world)}
            self.mode = self.modes["roam"]
            
        self.mode.enable()
        
        self.isRunning = True
        
        # create automatically some geometry to speed up work
        track = self.world.getTrack()
        for i in range(0,15):
            track.addRow()
            
        for cell in track.getCells():
            self.world.addEntity(cell)
    
    def _dumpNodes(self):
        render.ls()
        self.isRunning = False
    
    def _setupInput(self):
        self.ins.accept("escape", self.quit)
        if not wantsDirectTools():
            self.ins.accept("1", self._switchMode, ["roam"])
            self.ins.accept("2", self._switchMode, ["edit"])
            self.ins.accept("3", self._switchMode, ["drive"])
            self.ins.accept("4", self._switchMode, ["debug"])
            self.ins.accept("9", self._dumpNodes)
        
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
            taskMgr.step()
            sleep(self.FPS)
        else:
            render.analyze()
            # TODO do cleanup
            logger.info("Quitting application, have fun")


def wantsDirectTools():
    return ConfigVariableBool("want-directtools") is "t"

if __name__ == "__main__":
    e = Editor()
    e.run()
    