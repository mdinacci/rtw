# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
License: BSD

World Editor for SpeedBlazer


TODO

- install trac on website
* to deal with entities I need an Entity Manager (see also multifiles). 
  It's ok to have multiple references
  but there must be only a single place where to manage them.
* (re)code everything to use an EventManager (see taskMgr)
- track must be refactored in order to have an easier to sort geometry 
  I need a virtual node row to bind each group of five cells.
- delete entity (send event)
- change cell specific settings:
    - model (material, lights, texture)
    - color (optional)
- create multiple surfaces in ODE and bind them to cells ?
* implement scene save/load
- better ball physics (fix the fact that it never stops)
* input manager, the situation is getting out of control, who binds which key?
- better camera for the ball, must have constant X position and 
  constant Y distance
- new cell models to implement elevation
- curves :O
- fix the logger
- improve button location, now depends on the window' size
* Configuration manager, all the parameters must be read from disk
- use egg-qtess to polygonize a NURBS surface
- I need a python shell inside the editor !
 use Panda3D multifiles to store entities !
- search useless imports and remove them
* implement messaging system
- optimize scene. Have four nodes: staticobjs, actors, sky, evrthng with alpha
"""

# useful for debugging
from mdlib.decorator import traceMethod, accepts, trace, dumpArgs

# load configuration
# TODO the ConfigurationManager should take care of this
from pandac.PandaModules import loadPrcFile, ConfigVariableString, ConfigVariableBool
loadPrcFile("../res/Config.prc")
loadPrcFile("../res/Editor.prc")

# panda 3d stuff
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import Point3, Vec4, Vec3, NodePath, Quat
from pandac.PandaModules import LightAttrib, AmbientLight, DirectionalLight
from pandac.PandaModules import EggData, Filename
from pandac.PandaModules import WindowProperties

# collision to pick entities with mouse
from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, CollisionTraverser, CollisionRay, GeomNode

# panda utilities and actors
from mdlib.panda import eventCallback, inputCallback, Color, MouseWatcher
from mdlib.panda.core import *
from mdlib.panda.camera import *
from mdlib.panda.entity import *
from mdlib.panda.actor import *
from mdlib.panda.input import *
from mdlib.panda.physics import PhysicManager
from mdlib.panda import event

# logging
from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("editor", DEBUG)

# for debugging
import echo

# editor imports
from gui.wx import EditorGUI
from gui import GUIPresenter
#echo.echo_class(EditorGUI)

from sys import exit 

masterNode =  NodePath('editorNode')

def wantsDirectTools():
    return ConfigVariableBool("want-directtools") is "t"


class EditorScene(AbstractScene):
    def __init__(self, rootNode):
        super(EditorScene, self).__init__()
        self._rootNode = rootNode
        
        self._camera = None
        
        # subscribe to events ASAP
        self._subscribeToEvents()
        
        # create initial lights
        self._setupLights()
        
        # create some background entities to populate a bit the space 
        envPar = EnvironmentParams()
        envPar.parentNode = self._rootNode
        env = EnvironmentEntity(envPar)
        self.addEntity(env)    
    
    def _subscribeToEvents(self):
        pass
    
    def _setupLights(self):
        global masterNode
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
        masterNode.attachNewNode( directionalLight.upcastToPandaNode() )
        masterNode.attachNewNode( ambientLight.upcastToPandaNode() )
        masterNode.node().setAttrib( lAttrib )
    
    @eventCallback
    def deleteEntityFromNodePath(self, nodePath):   
        entityID = int(nodePath.getNetTag("ID"))
        nodePath.hideBounds()
        nodePath.removeNode()
        self.deleteEntityByID(entityID)
        
    def render(self):
        # FIXME Panda is doing everything now
        pass
    
    camera = property(fget=lambda self: self._camera, 
                      fset=lambda self,cam: setattr(self, '_camera', cam))
        
    
class EditorView(AbstractView):    
    INPUT_REFRESH_RATE = 1.0/60.0
    _dta = 0
    
    _scene = EditorScene(masterNode)
    
    def __init__(self, inputMgr):
        global masterNode
        super(EditorView, self).__init__(inputMgr)
        self.masterNode = masterNode

    def enable(self):
        # reenable camera controller
        self.camera.setActive(True)
        self.scene.camera = self.camera
        self._inputMgr.switchSchemeTo(self.INPUT_SCHEME)
    
    def disable(self):
        # disable camera controller
        self.camera.setActive(False)
        self._inputMgr.switchSchemeTo(BASE_SCHEME)
    
    def update(self, task):
        # entity position is updated automatically by the physic manager by 
        # setting parameters for position and rotation in params.
        # TODO
        # update GUI
        for entity in self.scene.getEntities():
            #if entity.isDirty:
            #logger.debug("Entity %s is dirty" % entity)
            if entity.ID == 51:
                entity.update()
            entity.isDirty = False
        
        self._inputMgr.update()
        self.scene.camera.update()
        
        return task.cont
    
    def render(self, task):
        self._scene.render()
        
        return task.cont

    def addEntityFromActor(self, actor):
        logger.debug("Adding new entity from actor: %s" % actor)
        if type(actor) is CellActor:
            self._scene.addEntity(CellEntity(actor.params))
        elif type(actor) is TheBallActor:
            self._scene.addEntity(TheBallEntity(actor.params))
    
    def _registerToCommands(self):
        self._inputMgr.bindEvent("escape", event.REQUEST_SHUTDOWN, 
                                 scheme="base")
        self._inputMgr.bindEvent("1", event.SWITCH_VIEW, ["roaming"], 
                                 scheme="base")
        self._inputMgr.bindEvent("2", event.SWITCH_VIEW, ["editing"], 
                                 scheme="base")
        self._inputMgr.bindEvent("3", event.SWITCH_VIEW, ["simulating"], 
                                 scheme="base")
        self._inputMgr.bindEvent("4", event.SWITCH_VIEW, ["debugging"], 
                                 scheme="base")
        self._inputMgr.bindCallback("0", self.scene.camera.lookAtOrigin)
        
    def _subscribeToEvents(self):
        pass

    scene = property(fget = lambda self: self._scene, fset=None)


class RoamingView(EditorView):
    """ 
    This mode allows to 'roam' freely inside the world. 
    """
    
    INPUT_SCHEME = "roaming"
    
    def _setupCamera(self):
        self.camera = RoamingCamera(self._inputMgr)
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)
        self.scene.camera = self.camera
    
    def _registerToCommands(self):
        super(RoamingView, self)._registerToCommands()
        self._inputMgr.createSchemeAndSwitch(self.INPUT_SCHEME)
        
    def enable(self):
        self.camera.showCursor(False)
        super(RoamingView, self).enable()


class EditingView(EditorView):
    """
    The editing view is the most sophisticated view. 
    It transform the editor in a world editor allowing to insert
    and to position objects.
    
    Messages sent here are received by the WxWindows GUI
    
    Accepted inputs:
    - space -> add a new row
    - mouse1 press -> select a node
    """
    
    INPUT_SCHEME = "editing"
          
    def __init__(self, inputMgr):
        super(EditingView, self).__init__(inputMgr)
        
        self._setupCollisionDetection()
        self._selectedObj = None

    def deleteSelectedObject(self):
        if self._selectedObj is not None:
            logger.debug("Deleting selected entity: %s " % self._selectedObj)
            #ID = self._selectedObj.ID
            #self.scene.deleteEntityByID(ID)
            ID = self._selectedObj.getNetTag("ID")
            self.scene.deleteEntityFromNodePath(self._selectedObj)
            self._selectedObj = None
        else:
            logger.info("Nothing selected, can't delete")

    def enable(self):
        self.camera.showCursor(True)
        super(EditingView, self).enable()
        
    def disable(self):
        super(EditingView, self).disable()
    
    @inputCallback
    def _onMousePress(self):
        global masterNode
        mousePos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.scene.camera, mousePos.getX(), 
                                   mousePos.getY())
        self.picker.traverse(masterNode)

        entries = self.pq.getNumEntries()
        logger.debug("Ray collided with %d entries" % entries)
        if entries > 0:
            if self._selectedObj is not None:
                self._selectedObj.hideBounds()
            self.pq.sortEntries()
            for i in range(0, entries):
                pickedObject = self.pq.getEntry(i).getIntoNodePath()
                logger.debug("Picked object #%d = %s" % (i, pickedObject))
            
            # highlight the closest selected object
            pickedObject = self.pq.getEntry(0).getIntoNodePath()
            pickedObject.showTightBounds()
            
            # set it current and send a msg that a new entity has been selected
            #self._selectedObj = self.scene.getEntityByID(pickedObject.getNetTag("ID"))
            self._selectedObj = pickedObject
            entity = self.scene.getEntityByID(pickedObject.getNetTag("ID"))
            logger.debug("Set selected object to: %s"  % entity)
            messenger.send(event.SELECT_ENTITY, [entity])
        else:
            logger.debug("No collisions at: %s" % mousePos)
    
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("entityPickRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
    
    def _setupCamera(self):
        self.camera = FixedCamera(self._inputMgr)
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)
        self.scene.camera = self.camera

    def _registerToCommands(self):
        super(EditingView, self)._registerToCommands()
        self._inputMgr.createSchemeAndSwitch(self.INPUT_SCHEME)
        self._inputMgr.bindEvent("space", event.NEW_ROW)
        self._inputMgr.bindCallback("mouse1", self._onMousePress)


class SimulatingView(EditorView):
    """
    This mode simulates the game.
    
    Accepted inputs:
    - i -> move the ball forward
    - j -> move the ball left
    - k -> move the ball back
    - l -> move the ball right
    """
    
    INPUT_SCHEME = "simulating"

    def __init__(self, inputMgr):
        super(SimulatingView, self).__init__(inputMgr)
        self._isPlayerSet = False

    def _setupCamera(self):
        self.camera = TheBallCamera(self._inputMgr)
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)
        self.scene.camera = self.camera
    
    def _registerToCommands(self):
        super(SimulatingView, self)._registerToCommands()
        self._inputMgr.createSchemeAndSwitch(self.INPUT_SCHEME)
        self._inputMgr.bindEvent("i", event.MOVE_PLAYER, [0,1.5,0])
        self._inputMgr.bindEvent("i-up", event.MOVE_PLAYER, [0,0,0])
        self._inputMgr.bindEvent("j", event.MOVE_PLAYER, [-2,0,0])
        self._inputMgr.bindEvent("j-up", event.MOVE_PLAYER, [0,0,0])
        self._inputMgr.bindEvent("k", event.MOVE_PLAYER, [0,-0.5,0])
        self._inputMgr.bindEvent("k-up", event.MOVE_PLAYER, [0,0,0])
        self._inputMgr.bindEvent("l", event.MOVE_PLAYER, [2,0,0])
        self._inputMgr.bindEvent("l-up", event.MOVE_PLAYER, [0,0,0])
        
    def setPlayer(self, actorID):
        entity = self.scene.getEntityByID(actorID)
        self.camera.setTarget(entity.nodePath)
        self._isPlayerSet = True
        logger.debug("Player set to: %s" % entity)
        
    def enable(self):
        global masterNode
        self.camera.showCursor(False)
        super(SimulatingView, self).enable()
        if not self._isPlayerSet:
            self.scene.camera.setTarget(masterNode)
            #self.scene.camera.setTarget(self.masterNode)
    
    
class Track(object):
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
    
    ROW_LENGTH = 5
    
    def __init__(self, parent):
        self._subscribeToEvents()
        self._nodePath = parent.attachNewNode("track")
        self._cells = []
        
    def getCellAtIndex(self, idx):
        logger.debug("Selecting cell at idx: %s" % idx)
        if idx < len(self._cells):
            return self._cells[idx]
        else:
            logger.error("Cell %d doesn't exists !" % idx)
            
    def createRow(self):
        rowID = len(self._cells)/self.ROW_LENGTH +1
        logger.debug("Creating row #%d" % rowID)
        rowNode = self._nodePath.attachNewNode("row-%d" % rowID)
        for i in range(0, self.ROW_LENGTH):
            yield self._createCell(rowNode)
    
    @eventCallback
    def changeNature(self, nature):
        for cell in self._cells:
            # TODO get entity and then change nature, can't do it on actor
            #cell.changeNature(nature)
            pass
            
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.CHANGE_NATURE, self.changeNature)
    
    def _createCell(self, parent):
        # by default put a new cell close to the latest added
        params = CellParams()
        
        if len(self._cells) > 0:
            prevPos = self._cells[-1].position
            if len(self._cells) % self.ROW_LENGTH == 0: 
                incX = - (self.ROW_LENGTH-1) * params.length
                incY = params.length
            else:
                incX = params.length
                incY = 0
            pos = Point3(prevPos.getX() + incX, prevPos.getY()+ incY, 
                         prevPos.getZ())
        else:
            pos = Point3(0,0,1)
        
        # set row, column tag; it makes easy to identify the cell after
        row = (len(self._cells)) / (self.ROW_LENGTH)
        col = (len(self._cells)) % (self.ROW_LENGTH)
        
        params.parentNode = parent
        params.position = pos
        params.color = Color.b_n_w[len(self._cells) % 2]
        params.posTag = "%d %d" % (row, col)
        cell = CellActor(params)
        
        logger.debug("Created cell #%d at row,col,pos (%d,%d,%s)" 
                     % (len(self._cells),row,col,pos))
        self._cells.append(cell)
        
        return cell
    

# TODO create actors and create geometry from here using the physic manager
class EditorLogic(AbstractLogic):
    """
    The editor is basically a world editor, specialised for the 
    SpeedBlazer game. It allows to construct the games by managing 3D objects,
    it allows also to debug and test the game.
    """
    def __init__(self, view):
        super(EditorLogic, self).__init__(view)
        self.physicMgr = PhysicManager()
        self._actors = []
        self._track = Track(self._view.masterNode)
        
        for i in range(0,10):
            self.addRow()
        
        # create player and hide it
        ballParams = TheBallParams()
        ballParams.parentNode = self._view.masterNode
        self._player = TheBallActor(ballParams)
        self._addActor(self._player)
        
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.NEW_ROW, self.addRow)
        self.listener.accept(event.DELETE_ENTITY_GUI, self._deleteActor)
        self.listener.accept(event.MOVE_PLAYER, self._movePlayer)
    
    @eventCallback
    def _movePlayer(self, xForce, yForce, zForce):
        logger.info("Moving player with vector force: %d,%d,%d" 
                    % (xForce, yForce, zForce))
        body = self._player.geom.getBody()
        speed = self._player.linearSpeed
        body.addForce(xForce*speed, yForce*speed, zForce*speed)
        entity = self.view.scene.getEntityByID(self._player.ID)
        entity.isDirty = True
        
    @eventCallback
    def _deleteActor(self, actorID):
        if actorID is not "" or actorID is not None:
            for _actor in self._actors:
                if _actor.ID == int(actorID):
                    logger.debug("Removing actor with ID: %s" % actorID)
                    self.physicMgr.removeGeometryTo(_actor)
                    self._actors.remove(_actor)
    
    @eventCallback    
    def addRow(self):
        for actor in self._track.createRow():
            self._addActor(actor)

    def showPlayer(self):
        logger.debug("Showing player")
        if hasattr(self._view,"setPlayer"):
            self._view.setPlayer(self._player.ID)
        self._view.scene.showEntityByID(self._player.ID)
        self.physicMgr.enableActor(self._player)
    
    def hidePlayer(self):
        """ Hide the ball as we need it only in simulating mode """ 
        logger.debug("Hiding player")
        self._view.scene.hideEntityByID(self._player.ID)
    
    def update(self, task):
        # TODO add state management
        self.physicMgr.update(self._actors)
        
        return task.cont
        
    def _addActor(self, actor) :
        logger.debug("Adding new actor: %s" % actor)
        actor.geom = self.physicMgr.createGeomForActor(actor)
        self._actors.append(actor)
        self._view.addEntityFromActor(actor)


class EditorApplication(AbstractApplication):
    REFRESH_RATE = 1.0/90.0
    dta = 0
    
    def __init__(self):
        super(EditorApplication, self).__init__()
        self._isRunning = True
        self._isPaused = False
        
    def shutdown(self):
        logger.info("Shutdown requested")
        self._isRunning = False
    
    def restore(self):
        self._isRunning = True
        self.dta = 0
        taskMgr.step()
        self.run()
    
    def _onMouseEnterPanda(self, args):
        self._isPaused = False
    
    def _onMouseLeavePanda(self, args):
        self._isPaused = True
    
    def run(self):
        """ 
        Main loop of the application 
        First step, create the processes that will be constantly updated
        Second, run them.
        Third, destroy them
        """
        
        # Create processes
        self._createProcesses()
        
        # Run processes
        import time
        while self._isRunning:
            if not self._isPaused:
                taskMgr.step()
            #self._gui.MainLoop()
            #self._mouseWatcher.update()
            time.sleep(0.001)
        else:
            self._shutDownProcesses()
            # TODO do cleanup
            logger.info("Quitting application, have fun")  
            
    def _createProcesses(self):
        # Start processes in the correct order
        # - logic update
        #    - physic update, logic takes care
        # - view update
        #    - input update view does it
        #    - scene update view does it
        #    - gui update   view does it
        # - view render
        #     - scene render view does it
        #     - gui render   view does it
        taskMgr.add(self._logic.update, "logic-update")
        taskMgr.add(self._view.update, "view-update")
        taskMgr.add(self._view.render, "view-render")
        taskMgr.add(self._gui.MainLoop, "wx-mainloop")
        taskMgr.add(self._mouseWatcher.update, "mw-update")
    
    def _shutDownProcesses(self):
        taskMgr.stop()
        self.nbase.userExit()
                
    @eventCallback
    def _switchView(self, view):
        if view in self._views.keys():
            # don't switch to the same view
            if self._view != self._views[view]:
                logger.debug("Switching to %s view" % view)
                self._view.disable()
                self._view = self._views[view]
                self._logic.view = self._view
                self._view.enable()
                
                #if view is "simulating":
                #    self._logic.showPlayer()
                #else:
                #    self._logic.hidePlayer()
                    
        else:
            logger.error("View %s doesn't exists" % view)
  
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.SWITCH_VIEW, self._switchView)
        self.listener.accept(event.REQUEST_SHUTDOWN, self.shutdown)
        #self.listener.accept(event.MOUSE_ENTER_PANDA, self._onMouseEnterPanda)
        #self.listener.accept(event.MOUSE_LEAVE_PANDA, self._onMouseLeavePanda)
  
    def _createLogicAndView(self):
        # TODO override ShowBase in order to use only what we really need
        self.nbase = ShowBase()
        self.nbase.windowType = "onscreen"
        masterNode.reparentTo(self.nbase.render)
        
        self._mouseWatcher = MouseWatcher(self.nbase)
        
        self._guiPresenter = GUIPresenter()
        self._gui = EditorGUI("gui/wx/gui.xrc", self._guiPresenter)
        
        h = self._gui.frame.GetHandle()
        wp = WindowProperties().getDefault()
        wp.setOrigin(0,0)
        wp.setSize(self._gui.frame.ClientSize.GetWidth(), self._gui.frame.ClientSize.GetHeight())
        wp.setParentWindow(h)
        self.nbase.openDefaultWindow(startDirect=False, props=wp)
        self._gui.setPandaWindow(self.nbase.win)
        
        inp = InputManager(self.nbase)
        
        self._views = {"editing": EditingView(inp),
                       "roaming": RoamingView(inp),
                       "simulating": SimulatingView(inp)}
        self._view = self._views["roaming"]
        self._view.enable()
        self._logic = EditorLogic(self._view)
        
        # don't change the order
        self._guiPresenter.setPandaController(self._views["editing"])
        self._guiPresenter.setView(self._gui)
        self._guiPresenter.setModel(self._views["editing"].scene)
        

a = echo.echo_class(EditorApplication)
if __name__ == "__main__":
    edApp = EditorApplication()
    edApp.run()
    