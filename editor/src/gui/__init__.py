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
        self._listener = SafeDirectObject()
        self._listener.accept(event.SELECT_ENTITY, self.onEntitySelect)
    
    """
    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
            print attr
            return self._pandaController.__dict__[attr]
    """
    
    def setView(self, view):
        """ Set the GUI object"""
        self._view = view
    
    def setPandaController(self, pandaController):
        """ 
        The panda controller is the game view, for the editor it 
        is always EditingView 
        """
        self._pandaController = pandaController
 
    def setModel(self, model):
        """ 
        Set the model that manage the entities in the Panda3D window 
        For the editor this is the GameScene object.
        """
        self._model = model
        self._view.onModelUpdate()
        
    def onShutDown(self):
        pass
    
    def getEntities(self):
        """ Returns the entities added to the scene. Called by the GUI. """
        items = []
        if self._model:
            items = self._model.getEntities()
            
        return items
        
    def getSceneGraphRoot(self):
        """ Returns the master node of the scene, called by the GUI """
        if self._model is not None:
            return self._model._rootNode
        
    # BEGIN WX WINDOWS CALLBACK CRAP
    
    def onNewButtonClicked(self, wxEvent):
        pass
    
    def onOpenButtonClicked(self, wxEvent):
        pass
    
    def onSaveButtonClicked(self, wxEvent):
        pass
    
    def onCopyButtonClicked(self, wxEvent):
        pass
    
    def onPasteButtonClicked(self, wxEvent):
        pass
    
    def onDeleteButtonClicked(self, wxEvent):
        """ Executed when the delete tool is clicked """
        self._pandaController.deleteSelectedObject()
    
    def onUndoButtonClicked(self, wxEvent):
        pass
    
    def onRedoButtonClicked(self, wxEvent):
        pass
    
    def onSceneGraphSelectionChange(self, wxEvent):
        pass
    
    # END WXWINDOWS CALLBACK CRAP
    
    # BEGIN PANDA EVENT CALLBACKS

    @eventCallback
    def onEntitySelect(self, entity):
        """ Executed when an entity is selected inside the panda window """
        logger.debug("Selecting entity %s " % entity)
        if hasattr(entity, "params"):
            props = entity.params.__dict__
            self._view.showEntityProperties(props)
    
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