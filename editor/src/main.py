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
import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import Point3, Vec4, Vec3, NodePath, Quat
from pandac.PandaModules import LightAttrib, AmbientLight, DirectionalLight
from pandac.PandaModules import EggData, Filename

# collision to pick entities with mouse
from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, CollisionTraverser, CollisionRay, GeomNode

# to draw the GUI
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText

# panda utilities and actors
from mdlib.panda import pandaCallback, eventCallback, inputCallback, SafeDirectObject, Color
from mdlib.panda.core import *
from mdlib.panda.camera import *
from mdlib.panda.entity import *
from mdlib.panda.actor import *
from mdlib.panda.physics import PhysicManager
from mdlib.panda.input import InputManager, Command, BASE_SCHEME
from mdlib.panda import event

# logging
from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("editor", DEBUG)

from sys import exit 


def wantsDirectTools():
    return ConfigVariableBool("want-directtools") is "t"


class EditViewGUI(object):
    """
    This GUI is used while editing the world in EditMode.
    It contains widgets that allow adding and modifying properties
    of the world. 
    
    TODO create the gui separately and use it here
    """
    def __init__(self, controller):
        self.controller = controller
        maps = loader.loadModel('delete_btn/delete_btn.egg')
        ra = base.camLens.getAspectRatio()
        
        self.leftMenu = DirectFrame(parent=aspect2d,
                                    frameColor=(0,0,1,.3), 
                                    frameSize=(-1.5,0.7,-1.5,0.7),
                                    pos = (-.8*ra,0,.6*ra))
        
        self._widgets = [self.leftMenu]
        
        deleteBtn = DirectButton(geom = (maps.find('**/delete'),
                         maps.find('**/delete'),
                         maps.find('**/delete_over'),
                         maps.find('**/delete')),
                         borderWidth=(0,0),
                         frameColor=(0,0,0,0),
                         scale = .1,
                         pos = (-.1,0,-.4),
                         command=self.controller.onDeleteButtonClick)
        deleteBtn.hide()
        self._widgets.append(deleteBtn)
        
        worldMenu = DirectOptionMenu(text="World Type", scale=0.1,
                                        items=["Mountain","Space","Forest"],
                                        initialitem=0, 
                                        borderWidth=(0,0),
                                        highlightColor=(0.65,0.65,0.65,1),
                                        pos = (-.2,0,0),
                                        command=self.controller.onWorldButtonClick)
        worldMenu.hide()
        self._widgets.append(worldMenu)

        cellTypeMenu = DirectOptionMenu(text="Cell Type", scale=0.1,
                                        items=["Normal","Speed","Jump","Teleport",
                                               "Invert","Bounce Back"],
                                        initialitem=0, 
                                        borderWidth=(0,0),
                                        highlightColor=(0.65,0.65,0.65,1),
                                        pos = (-.2,0,-.2),
                                        command=self.controller.onCellNatureClick)
        cellTypeMenu.hide()
        self._widgets.append(cellTypeMenu)
        
        for widget in self._widgets[1:]:
            widget.reparentTo(self.leftMenu)
        
    @eventCallback
    def editNode(self, nodepath):
        # show properties editor
        pass
        
    def enable(self):
        for widget in self._widgets:
            widget.show()
    
    def disable(self):
        for widget in self._widgets:
            widget.hide()


class EditorScene(AbstractScene):
    def __init__(self, parentNode):
        super(EditorScene, self).__init__()
        self._parentNode = parentNode
        
        self._camera = None
        
        # subscribe to events ASAP
        self._subscribeToEvents()
        
        # create initial lights
        self._setupLights()
        
        # create some background entities to populate a bit the space 
        envPar = EnvironmentParams()
        envPar.parentNode = self._parentNode
        env = EnvironmentEntity(envPar)
        self.addEntity(env)    
    
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.DELETE_ENTITY_GUI, 
                             self.deleteEntityFromNodePath)
    
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
    
    # All the objects are attached to the master node
    masterNode = render.attachNewNode("editorNode")
    _scene = EditorScene(masterNode)
    
    def __init__(self):
        super(EditorView, self).__init__()
        #self._scene = EditorScene(self.masterNode)

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
     
    def enable(self):
        # reenable camera controller
        #self.scene.camera.enable()
        self.camera.setActive(True)
        self.scene.camera = self.camera
        self._inputMgr.switchSchemeTo(self.INPUT_SCHEME)
    
    def disable(self):
        # disable camera controller
        #self.scene.camera.disable()
        self.camera.setActive(False)
        self._inputMgr.switchSchemeTo(BASE_SCHEME)
    
    def update(self):
        # update GUI
        # update input
        for entity in self.scene.getEntities():
            #if entity.isDirty:
            #logger.debug("Entity %s is dirty" % entity)
            if entity.ID == 51:
                entity.update()
            entity.isDirty = False
        
        self._inputMgr.update()
        # TODO update entities position !
        self.scene.camera.update()
    
    def render(self):
        self._scene.render()

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
    
    Accepted inputs:
    - space -> add a new row
    - mouse1 press -> select a node
    """
    
    class GUIControllerDelegate(object):
        def __init__(self, editView):
            # Inner classes don't have access to the outer
            # class attributes like in Java :(
            self._view = editView
        
        def __getattr__(self,attr):
            try:
                return self.__dict__[attr]
            except KeyError, e:
               return self._view.__dict__[attr]
           
        @pandaCallback
        def onDeleteButtonClick(self):
            if self._selectedObj is not None:
                logger.debug("Deleting selected entity %s: " % self._selectedObj)
                messenger.send(event.DELETE_ENTITY_GUI, [self._selectedObj])
                self._view._selectedObj = None
            else:
                logger.info("Nothing selected, can't delete")
            
        @pandaCallback
        def onWorldButtonClick(self, selection):
            logger.debug("Selected %s" % selection)
            messenger.send(event.CHANGE_NATURE, [selection])
        
        @pandaCallback
        def onCellNatureClick(self, selection):
            logger.debug("Selected %s" % selection)
            if self._selectedObj is not None:
                self._selectedObj.changeNature(selection)
            #messenger.send("change-cell-nature", [selection])
    
    INPUT_SCHEME = "editing"
          
    def __init__(self):
        # the GUI must be created first in order to bind its methods
        self._gui = EditViewGUI(self.GUIControllerDelegate(self))
        self._gui.disable()

        super(EditingView, self).__init__()
        
        self._setupCollisionDetection()
        self._selectedObj = None

    def enable(self):
        self.camera.showCursor(True)
        super(EditingView, self).enable()
        self._gui.enable()
        
    def disable(self):
        super(EditingView, self).disable()
        self._gui.disable()
    
    @inputCallback
    def _onMousePress(self):
        mousePos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.scene.camera, mousePos.getX(), 
                                   mousePos.getY())
        self.picker.traverse(self.masterNode)

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
            self._selectedObj = pickedObject
            messenger.send(event.SELECT_ENTITY, [self._selectedObj])
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

    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.SELECT_ENTITY, self._gui.editNode)
    
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

    def __init__(self):
        super(SimulatingView, self).__init__()
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
        self.camera.showCursor(False)
        super(SimulatingView, self).enable()
        if not self._isPlayerSet:
            self.scene.camera.setTarget(self.masterNode)
    
    
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
        
        params.parentNode = self._nodePath
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
        #self.hidePlayer()
        
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
    def _deleteActor(self, actor):
        actorID = actor.getNetTag("ID")
        print actorID
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
    
    def update(self):
        # TODO add state management
        self._view.update()
        self.physicMgr.update(self._actors)
        taskMgr.step()
        
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
        
    @eventCallback
    def _switchView(self, view):
        if view in self._views.keys():
            # don't switch to the same view
            if self._view != self._views[view]:
                logger.debug("Switching to %s view" % view)
                # TODO consider sending event 
                self._view.disable()
                self._view = self._views[view]
                self._logic.view = self._view
                # TODO consider sending event 
                self._view.enable()
                
                if view is "simulating":
                    self._logic.showPlayer()
                else:
                    self._logic.hidePlayer()
                    
        else:
            logger.error("View %s doesn't exists" % view)
  
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.SWITCH_VIEW, self._switchView)
        self.listener.accept(event.REQUEST_SHUTDOWN, self.shutdown)
  
    def _createLogicAndView(self):
        self._views = {"editing": EditingView(),
                       "roaming": RoamingView(),
                       "simulating": SimulatingView()}
        self._view = self._views["roaming"]
        self._view.enable()
        self._logic = EditorLogic(self._view)
        
    def shutdown(self):
        logger.info("Shutdown requested")
        self._isRunning = False
    
    def restore(self):
        self._isRunning = True
        self.dta = 0
        taskMgr.step()
        self.run()
    
    def run(self):
        import time
        while self._isRunning:
            self.dta += globalClock.getDt()
            while self.dta > self.REFRESH_RATE:
                self.dta -= self.REFRESH_RATE
                self._logic.update()
                self._view.render()
            time.sleep(0.01)
        else:
            taskMgr.stop()
            #render.analyze()
            # TODO do cleanup
            logger.info("Quitting application, have fun")  
            
a = EditorApplication
if __name__ == "__main__":
    edApp = EditorApplication()
    edApp.run()
    