# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
License: BSD

World Editor


TODO

- install trac on website
* to deal with entities I need an Entity Manager (see also multifiles). 
  It's ok to have multiple references
  but there must be only a single place where to manage them.
* (re)code everything to use an EventManager (see taskMgr)
- change cell specific settings:
    - model (material, lights, texture)
    - color (optional)
- create multiple surfaces in ODE and bind them to cells ?
* implement scene save/load
- better ball physics (fix the fact that it never stops)
- better camera for the ball, must have constant X position and 
  constant Y distance
- new cell models to implement elevation
- curves :O
- fix the logger
* Configuration manager, all the parameters must be read from disk
- use egg-qtess to polygonize a NURBS surface
- I need a python shell inside the editor !
- use Panda3D multifiles to store entities !
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
from pandac.PandaModules import EggData, Filename, BamFile
from pandac.PandaModules import WindowProperties

# collision to pick entities with mouse
from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, CollisionTraverser, CollisionRay, GeomNode

# panda utilities and actors
from mdlib.panda import eventCallback, inputCallback, guiCallback, MouseWatcher
from mdlib.panda.core import *
from mdlib.panda.camera import *
from mdlib.panda.entity import *
from mdlib.panda.actor import *
from mdlib.panda.input import *
from mdlib.panda.data import *
from mdlib.panda.entity import *
from mdlib.panda.physics import POM
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

import cPickle
from sys import exit 


class EditorScene(AbstractScene):
    def __init__(self):
        super(EditorScene, self).__init__()
        self._camera = None
        
        # subscribe to events ASAP
        self._subscribeToEvents()
        
        # create initial lights
        self._setupLights()
        
    
    def _subscribeToEvents(self):
        # must be overridden
        pass
    
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
        
        self._rootNode.attachNewNode( directionalLight.upcastToPandaNode() )
        self._rootNode.attachNewNode( ambientLight.upcastToPandaNode() )
        self._rootNode.node().setAttrib( lAttrib )
    
    """
    def deleteEntityFromNodePath(self, nodePath):   
        # FIXME must remove entity IF it is an entity (maybe just a tree)
        nodePath.hideBounds()
        nodePath.removeNode()
    """
     
    def render(self):
        # FIXME Panda is doing everything now
        pass
    
    camera = property(fget=lambda self: self._camera, 
                      fset=lambda self,cam: setattr(self, '_camera', cam))
        
    
class EditorView(AbstractView):    
    INPUT_REFRESH_RATE = 1.0/60.0
    _dta = 0
    
    _scene = EditorScene()
    
    def __init__(self, inputMgr):
        super(EditorView, self).__init__(inputMgr)

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
        self._inputMgr.update()
        self.scene.camera.update()
        self.scene.update()
        
        return task.cont
    
    def render(self, task):
        self.scene.render()
        
        return task.cont

    def setSceneRootNode(self, node):
        self.scene.setRootNodeParent(node)

    def addToScene(self, entity):
        self._scene.addEntity(entity)
   
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

    def getSelectedEntity(self):
        if self._selectedObj is not None:
            entity = self.scene.getEntityByID(int(self._selectedObj.getNetTag("UID")))
            return entity

    def deleteFromScene(self, entity):
        self.scene.deleteEntity(entity)

    def deleteSelectedObject(self):
        if self._selectedObj is not None:
            logger.debug("Deleting selected entity: %s " % self._selectedObj)
            
            self.scene.deleteEntityByID(int(self._selectedObj.getNetTag("UID")))
            #self.scene.deleteEntityFromNodePath(self._selectedObj)
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
        mousePos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.scene.camera, mousePos.getX(), 
                                   mousePos.getY())
        self.picker.traverse(self.scene.getRootNode())

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
            entity = self.scene.getEntityByID(pickedObject.getNetTag("UID"))
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
        self.camera.setTarget(entity.render.nodepath)
        self._isPlayerSet = True
        logger.debug("Player set to: %s" % entity)
        
    def enable(self):
        self.camera.showCursor(False)
        super(SimulatingView, self).enable()


# TODO create actors and create geometry from here using the physic manager
class EditorLogic(AbstractLogic):
    """
    The editor allows to construct the games by managing 3D objects,
    it allows also to debug and test the game.
    """
    def __init__(self, view):
        super(EditorLogic, self).__init__(view)
        
        self.loadScene("/tmp/test.rtw")
        
        """
        # create some background entities to populate a bit the space 
        self.view.addToScene(GOM.createEntity(environment_params.copy()))    
        
        self._track = GOM.createEntity(track_params.copy())
        self.view.addToScene(self._track)
        
        for i in range(0,5):
            self.addRow()
        
        # create player
        self._player = GOM.createEntity(ball_params.copy())
        self.view.addToScene(self._player)
        #"""
        
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.NEW_ROW, self.addRow)
        self.listener.accept(event.MOVE_PLAYER, self._movePlayer)
    
    @eventCallback
    def _movePlayer(self, xForce, yForce, zForce):
        logger.info("Moving player with vector force: %d,%d,%d" 
                    % (xForce, yForce, zForce))
        body = self._player.physics.geom.getBody()
        speed = self._player.physics.linearSpeed
        body.addForce(xForce*speed, yForce*speed, zForce*speed)
        entity = self.view.scene.getEntityByID(self._player.UID)
        entity.isDirty = True
    
    @eventCallback    
    def addRow(self):
        for entity in self._track.createRow():
            self.view.addToScene(entity)

    @guiCallback
    def loadScene(self, sceneFile):
        fh = open(sceneFile, "rb")
        
        # load function
        load = lambda: cPickle.load(fh)
        
        version = load()
        entitiesNum = load()
        
        entities = [self.view.addToScene(GOM.createEntity(load())) 
                    for idx in range(0, entitiesNum)]
        
        # set player and track
        #self._player = self.view.getEntityByName("Ball")
        #self._track = self.view.getEntityByName("Track")
        
    
    @guiCallback
    def saveScene(self, sceneFile):
        # TODO save to a multifile
        fh = open('/tmp/test.rtw', "wb")
        
        # save function
        dump = lambda x: cPickle.dump(x, fh, -1)
        
        # get the serialised data from the scene
        entities = self.view.scene.serialise()
        
        # store version
        dump("v0.1")
        
        # store the number of entities, useful when unpickling
        dump(len(entities))
        
        # save entities
        [dump(entity) for entity in entities]
        
        fh.close()
        
        logger.info("Scene file saved to %s" % sceneFile )
    
    @guiCallback
    def deleteSelectedObject(self):
        entity = self.view.getSelectedEntity()
        if entity.has_key("physics") and entity.physics.has_key("geom"):
            POM.removeGeometryTo(entity)
        self.view.deleteFromScene(entity)

    def showPlayer(self):
        logger.debug("Showing player")
        if hasattr(self._view,"setPlayer"):
            self._view.setPlayer(self._player.UID)
    
    def hidePlayer(self):
        """ Hide the ball as we need it only in simulating mode """ 
        logger.debug("Hiding player")
        self._view.scene.hideEntityByID(self._player.UID)
    
    def update(self, task):
        # TODO add state management
        POM.update(self.view.scene.getActors())
        
        return task.cont
        

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
        pass
        #self._isPaused = False
    
    def _onMouseLeavePanda(self, args):
        pass
        #self._isPaused = True
    
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
                
                if view is "simulating":
                    self._logic.showPlayer()
        else:
            logger.error("View %s doesn't exists" % view)
  
    def _subscribeToEvents(self):
        self.listener = SafeDirectObject()
        self.listener.accept(event.SWITCH_VIEW, self._switchView)
        self.listener.accept(event.REQUEST_SHUTDOWN, self.shutdown)
        self.listener.accept(event.MOUSE_ENTER_PANDA, self._onMouseEnterPanda)
        self.listener.accept(event.MOUSE_LEAVE_PANDA, self._onMouseLeavePanda)
  
    def _createLogicAndView(self):
        # TODO override ShowBase in order to use only what we really need
        self.nbase = ShowBase()
        self.nbase.windowType = "onscreen"
        
        #taskMgr.popupControls()
        
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
        self._view.setSceneRootNode(self.nbase.render)
        self._logic = EditorLogic(self._view)
        
        # don't change the order
        #self._guiPresenter.setPandaController(self._views["editing"])
        self._guiPresenter.setPandaController(self._logic)
        self._guiPresenter.setView(self._gui)
        # FIXME
        self._guiPresenter.setModel(self._views["editing"].scene)
        

a = echo.echo_class(EditorApplication)
if __name__ == "__main__":
    edApp = EditorApplication()
    edApp.run()
    