# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

This module contains the most important classes on an application.
They must be used as a starting point for a new game.
"""

__all__= ["AbstractApplication", "ApplicationState", "AbstractView", 
          "AbstractLogic", "AbstractScene"]

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("core", DEBUG)

from mdlib.panda import event

from input import InputManager

class AbstractApplication(object):
    """
    The application layer is the object that holds all the operating system
    dependent systems, initialisation, localised strings, resource cache 
    and so on.
    """
    
    def __init__(self):
        """ 
        Initialisation:
        
        - detect multiple instance of the application 
        - load language specific settings
        - check memory and secondary storage space
        - load the game's resource cache
        - initialise window for application
        - create game logic and game views
        - create the display device
        - load the game data
        """
        self._subscribeToEvents()
        self._createLogicAndView()

    def _subscribeToEvents(self):
        raise NotImplementedError()
    
    def _createLogicAndView(self):
        """
        create a game (logic)
        create a view
        attach the view to the game
        return the game
        """
        pass
    
    def run(self):
        raise NotImplementedError()
    
    def shutdown(self):
        raise NotImplementedError()
    

# use Panda FSM
class ApplicationState(object):
    """ 
    Manage the application state, which can be:
    - Initialise
    - Run
    - Pause
    - Quit
    - Debug (?)
    """
    pass


class AbstractView(object):
    """
    The game view's job is to present the game, accept input and translate
    that input into commands for the game logic.
    It contains a GameScene to draw the 3D world and the user interface, a 
    listener to handle events coming from the game logic and a controller to 
    reads input from the keyboard and mouse and translates input into commands
    that are sent to the game logic.
    """
    #_inputMgr = InputManager()
    
    def __init__(self, inputManager):
        self._inputMgr = inputManager
        self._setupCamera()
        self._registerToCommands()
        self._subscribeToEvents()
    
    def _setupCamera(self):
        raise NotImplementedError()
    
    def _registerToCommands(self):
        raise NotImplementedError()
    
    def _subscribeToEvents(self):
        """ Register to events coming from the game logic """
        raise NotImplementedError()
    
    def getScene(self):
        raise NotImplementedError()
    
    def enable(self):
        """ Activate this scene """
        raise NotImplementedError()
    
    def disable(self):
        """ Deactivate this scene """
        raise NotImplementedError()
    
    def update(self):
        """ 
        Update this view, normally it means updating the 
        entities that made part of the scene, reading user input, updating the
        GUI etc...  """
        raise NotImplementedError()
    
    def render(self):
        """
        Render the scene. For the moment Panda3D is doing everything 
        automatically but this behavior must be changed
        """
        # base.graphicsEngine.renderFrame()
        # render GUI ?
        raise NotImplementedError()
    

class AbstractLogic(object):
    """
    Stores the game logic
    """

    def __init__(self, view):
        """
        - create physics
        - register to events
        - register to game commands
        - if scene != None load the scene, otherwise create a new empty one
        """
        self._view = view
        #self._eventMgr = EventManager()
        self._subscribeToEvents()
        pass
    
    def _subscribeToEvents(self):
        raise NotImplementedError()
    
    def update(self):
        """ 
        Called once per game loop, may be called at a different rate than the 
        rendering loop.
        - update game logic specific stuff
        - update physics 
        """
        raise NotImplementedError()
    
    view = property(fget=lambda self: self._view, 
                    fset=lambda self,view: setattr(self, '_view', view))
        

class AbstractScene(object):
    """
    A Scene contains all the 3D objects that make up the game
    """
    def __init__(self):
        self._entities = []
        
    def addEntity(self, entity):
        """ Add a new entity to the scene """
        
        logger.debug("Adding entity %s to scene" % entity)
        self._entities.append(entity)
        self._entities.sort(key=lambda obj: obj.ID)

    def deleteEntityByID(self, entityID):
        """ Delete an entity from a scene given its entity ID """
        
        entity = self.getEntityByID(entityID)
        if entity is not None:
            logger.debug("Removing entity %s from scene" % entity)
            self._entities.remove(entity)
            messenger.send(event.DELETE_ENTITY_GUI, [entityID])
        else:
            s = "Cannot delete entity (maybe it's inside a model?) %s"
            logger.warning(s % entity)
    
    def getEntityByID(self, entityID):
        """ Returns an entity given its ID """
        
        # entity ID is stored as an int in entity params but as a string
        # in the nodepath tag
        if type(entityID) is str:
            entityID = int(entityID)
        # simple linear search
        for entity in self._entities:
            if entity.ID == entityID:
                return entity
        else:
            logger.warning("No entity returned for ID: %s" % entityID)
        
    def hideEntityByID(self, entityID):
        """ Hide an entity from the scene. The node is stashed """
        entity = self.getEntityByID(entityID)
        logger.debug("Hiding entity %s" % entity)
        entity.nodePath.stash()
        
    def showEntityByID(self, entityID):
        """ Hide an entity from the scene. The node is unstashed """
        entity = self.getEntityByID(entityID)
        logger.debug("Showing entity %s" % entity)
        entity.nodePath.unstash()
        
    def getEntities(self):
        return self._entities
    
    def render(self):
        # TODO raise exception
        pass
    
    def ls(self):
        """ Debug function to list all the entities in the scene """
        logger.debug("Listing entities in scene:" )
        for entity in self._entities:
            logger.debug("Entity: %s" % entity)
        logger.debug("Listing finished")

