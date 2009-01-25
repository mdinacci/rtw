# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("gui-controller", DEBUG)

from mdlib.panda.input import SafeDirectObject
from mdlib.panda import event
from mdlib.panda import eventCallback, guiCallback

from gui.qt.model import SceneGraphModel, EntityInspectorModel

class GUICommand(object):
    def __init__(self, oneliner):
        self._oneliner = oneliner
    
    def __str__(self):
        return self._oneliner

    def do(self):
        pass
    
    def undo(self):
        pass
 
 
class GUIPresenter(object):
    """
    This class is a proxy for Panda events that may change GUI widgets.
    It also receives calls from the GUI that updates the Model and in turn
    update the EditingView.
    
    Ex.1:
    - User select an entity
    - Panda intercepts the mouse press and send a SELECT_ENTITY event
    - The GUIPresenter receives the event and update the property grid with
      the parameters of the selected entity.
    Ex.2:
    - After having selected an entity, the user clicks on the delete button
    - The GUI notify the GUIPresenter that in turns notify the model.
    - The model sent an event that is received by the panda controller 
      (EditingView) 
    """
    def __init__(self):
        self._pandaController = None
        self._model = None
        self._view = None
        self._listener = SafeDirectObject()
        self._listener.accept(event.SELECT_ENTITY, self.onEntitySelect)
        self._listener.accept(event.ENTITY_DELETED, self.onEntityDeleted)
        self._listener.accept(event.ENTITY_ADDED, self.onEntityAdded)
        
        self._sceneGraphModel = SceneGraphModel()
        self._entitiesModel = EntityInspectorModel()
    
    def setIdleCallback(self, idleCallback):
        self._idleCallback = idleCallback
    
    def idleCallback(self):
        self._idleCallback()
    
    def setView(self, view):
        """ Set the GUI object"""
        self._view = view
    
    def setPandaController(self, pandaController):
        """ 
        The panda controller is the game view, for the editor it 
        is always EditingView 
        """
        self._pandaController = pandaController
 
    def setModel(self, model=None):
        """ 
        Set the model that manage the entities in the Panda3D window 
        For the editor this is the GameScene object.
        """
        if model is not None:
            self._model = model
            self._entitiesModel.populate(self._model.getEntities().values())
            self._sceneGraphModel.populate(self.getSceneGraphRoot())
        
        if self._view is not None:
            self._view.sceneGraphView.setModel(self._sceneGraphModel)
            self._view.entityInspector.setModel(self._entitiesModel)
            # FIXME should be in the view code, but it's just one line...
            # move it as soon as the code become more complicated
            self._view.sceneGraphView.expandAll()
        
    def onShutDown(self):
        pass
    
    def getEntities(self):
        """ Returns the entities added to the scene. Called by the GUI. """
        items = []
        if self._model:
            items = self._model.getEntities()
            
        return items
    
    def getSceneGraphModel(self):
        return self._sceneGraphModel
    
    def getEntitiesModel(self):
        return self._entitiesModel
    
    def getSceneGraphRoot(self):
        """ Returns the master node of the scene, called by the GUI """
        if self._model is not None:
            return self._model._rootNode
        
    # BEGIN GUI CALLBACKS
    
    def onNewButtonClicked(self):
        # ask if wants to save
        # erase scene
        pass
    
    def onOpenButtonClicked(self):
        """ Executed when the open tool is clicked """
        loadFile = self._view.getLoadedFile()
        self._pandaController.loadScene(loadFile)
    
    def onSaveButtonClicked(self):
        """ Executed when the save tool is clicked """
        if self._pandaController.hasSavedScene():
            self._pandaController.saveScene(self._pandaController.getSavedScene())
        else:
            self.onSaveAsButtonClicked()
    
    def onSaveAsButtonClicked(self):
        """ Executed when the save as tool is clicked """
        saveFile = self._view.getSaveFile()
        self._pandaController.saveScene(saveFile)
        
    def onCopyButtonClicked(self):
        """ Executed when the copy tool is clicked """
        self._pandaController.copySelectedObject()
    
    def onPasteButtonClicked(self):
        """ Executed when the paste tool is clicked """
        self._pandaController.pasteSelectedObject()
    
    def onDeleteButtonClicked(self):
        """ Executed when the delete tool is clicked """
        self._pandaController.deleteSelectedObject()
    
    def onQuitButtonClicked(self):
        """ Executed when the quit tool is clicked """
        pass
    
    def onUndoButtonClicked(self):
        pass
    
    def onRedoButtonClicked(self):
        pass
    
    def onSceneGraphSelectionChange(self):
        print "IMPLEMENT ME: onSceneGraphSelectionChange"
    
    def onEntityInspectorSelectionChanged(self, index):
        print "IMPLEMENT ME: onEntityInspectorSelectionChanged"
    
    def onEntityPropertyModified(self, eid, prop, newValue):
        logger.debug("Entity modified, updating view")
        self._pandaController.editObject(eid, prop, newValue)
        
        
    # END GUI CALLBACKS
    
    # BEGIN PANDA EVENT CALLBACKS

    @eventCallback
    def onEntitySelect(self, entity):
        """ Executed when an entity is selected inside the panda window """
        logger.debug("Selecting entity %s " % entity)

        # get qmodelidx from model
        # on view collapse and expand the qmodelidx node
        sgIndex = self._sceneGraphModel.getIndexForEntityID(entity.UID)
        eiIndex = self._entitiesModel.getIndexForEntityID(entity.UID)
        
        self._view.highlightNodes(sgIndex, eiIndex)
    
    @eventCallback
    def onEntityDeleted(self, entityID):
        logger.debug("Entity deleted, updating view")
        self.setModel(self._model)
        
    @eventCallback
    def onEntityAdded(self, entity):
        logger.debug("Entity added, updating view")
        self.setModel(self._model)
    
    
    # END PANDA EVENT CALLBACKS

    """
    def onWorldButtonClick(self, selection):
        logger.debug("Selected %s" % selection)
        messenger.send(event.CHANGE_NATURE, [selection])
    
    def onCellNatureClick(self, selection):
        logger.debug("Selected %s" % selection)
        if self._selectedObj is not None:
            self._selectedObj.changeNature(selection)
        #messenger.send("change-cell-nature", [selection])
    """