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

from pandac.PandaModules import NodePath

from mdlib.panda import event
from mdlib.panda.data import EntityType, KeyValueObject

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
        self._rootNode = NodePath("Scene")
        self._rootNode.setTag("UID","-999")
        self._noneNode = self._rootNode.attachNewNode("Non-Render")
        self._rootNode.setTag("UID","-998")
        self._staticNode = self._rootNode.attachNewNode("Static")
        self._rootNode.setTag("UID","-997")
        self._actorsNode = self._rootNode.attachNewNode("Actors")
        self._rootNode.setTag("UID","-996")
        self._envNode = self._rootNode.attachNewNode("Background")
        self._rootNode.setTag("UID","-995")
        self._alphasNode = self._rootNode.attachNewNode("Alphas")
        self._rootNode.setTag("UID","-994")
        
         # data structure for game objects
        self._entities = {}
        
        # entities that needs to be updated
        self._dirtyEntities = {}
    
    def getActors(self):
        return [entity for entity in self._entities.values() \
                  if entity.render.entityType == EntityType.ACTOR]
        
    def addEntity(self, entity):
        """ Add a new entity to the scene """
        
        logger.debug("Adding entity %s to scene" % entity)
        # setup parent node
        if not entity.render.has_key("parentNode"):
            rp = entity.render.entityType
            destNode = None
            if rp == EntityType.NONE:
                entity.render.parentNode = self._noneNode
                destNode = self._noneNode
            elif rp == EntityType.ACTOR:
                entity.render.parentNode = self._actorsNode
                destNode = self._actorsNode
            elif rp == EntityType.STATIC:
                entity.render.parentNode = self._staticNode
                destNode = self._staticNode
            elif rp == EntityType.BACKGROUND:
                entity.render.parentNode = self._envNode
                destNode = self._envNode
            elif rp == EntityType.ALPHAS:
                entity.render.parentNode = self._alphasNode
                destNode = self._alphasNode
            else:
                logger.error("Unknown render pass, adding node to root node")
                destNode = self._noneNode
                entity.render.parentNode = self._rootNode
        else:
            if type(entity.render.parentNode) is NodePath: # a nodepath
                destNode = entity.render.parentNode
            else: # an ID
                parentEntity = self.getEntityByID(entity.render.parentNode)
                destNode = parentEntity.render.nodepath
                entity.render.parentNode = destNode
        
        entity.render.nodepath.reparentTo(destNode)

        self._entities[entity.UID] = entity
        self._dirtyEntities[entity] = []
        
        messenger.send(event.ENTITY_ADDED, [entity])
    
    def getEntityByName(self, entityName):
        for entity in self._entities.values():
            if entity.prettyName == entityName:
                return entity
       
    def getEntityByID(self, entityID):
        eid = int(entityID)
        if self._entities.has_key(eid):
            return self._entities[eid]

        return None
    
    def deleteEntity(self, entity):
        logger.debug("Deleting entity %d (total: %s)" % (entity.UID,
                                                         len(self._entities)))
        uid = entity.UID
        
        # destroy node
        entity.render.nodepath.hideBounds()
        entity.render.nodepath.removeNode()
        
        # remove from maps
        if self._dirtyEntities.has_key(entity):
            del self._dirtyEntities[entity]
        del self._entities[entity.UID]
        
        # send notification
        messenger.send(event.ENTITY_DELETED, [uid])
    
    def deleteEntityByID(self, entityID):
        logger.debug("Deleting entity %d from scene " % entityID)
        entity = self.getEntityByID(entityID)
        if entity != None:
            self.deleteEntity(entity)
            
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
    
    def editEntity(self, eid, propPath, newValue):
        """ Change the property of an entity """
        
        logger.debug("Updating entity %s with value %s for property %s" \
                     % (eid, propPath, newValue ) )
        
        entity = self.getEntityByID(eid)

        print "BEFORE: ", entity.prettyName
        
        # set the new property value, a bit hackish..
        tokens = propPath.split(".")
        if len(tokens) > 1:
            prev = entity[tokens[0]]
            print prev
            for token in tokens[1:]:
                if token == tokens[-1]:
                    prev[token] = newValue
                    print prev
                else:
                    prev = prev.get(token)
                    print prev
        else:
            entity[propPath] = newValue

        if self._dirtyEntities.has_key(entity):
            self._dirtyEntities[entity].append(propPath)
        else:
            self._dirtyEntities[entity] = [propPath]
            
        print "AFTER: ", entity.prettyName
        
    def setRootNodeParent(self, node):
        self._rootNode.reparentTo(node)
    
    def getRootNode(self):
        return self._rootNode
    
    def getEntities(self):
        return self._entities
    
    def update(self):
        for entity in self._dirtyEntities():
            """ update...complicated, the code depends on the specific 
            properties that need to be updated """
    
    def render(self):
        pass

    def serialise(self):
        # no need to serialise the root node as it will be recreated
        return [entity.serialise() for entity in self._entities.values()]
    
    def ls(self):
        """ Debug function to list all the entities in the scene """
        logger.debug("Listing entities in scene:" )
        for entity in self._entities:
            logger.debug("Entity: %s" % entity)
        logger.debug("Listing finished")

