# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("data", DEBUG)

from mdlib.patterns import singleton
from mdlib.panda.physics import POM 

from pandac.PandaModules import Point3, Quat, BitMask32, Vec4, Material
from pandac.PandaModules import NodePath, Filename, ActorNode
from direct.showbase.Loader import Loader
from direct.directtools.DirectGeometry import LineNodePath

from UserDict import DictMixin

__all__ = ["KeyValueObject", "ResourceLoader", "GOM"]


def bitMaskToInt(bitmask):
    # [1:-1] to remove first white space and latest \n
    s = "".join(str(bitmask)[1:-1].split(" "))
    num = 0
    for c in s:
        if c is "1":
            num += 2**int(c)
            
    return num


# TODO move from here
class EntityType:
    NONE  = 0x0   # non renderable objects (triggers, lights, cameras etc..)
    STATIC = 0x1  # environments and level geometry
    ACTOR = 0x2   # things that have a physic geometry and eventually a body
    BACKGROUND = 0x3 # the background "behind" everything
    ALPHA = 0x4   # alpha objects
    PLAYER = 0x5 # player object

    
class ResourceLoader(Loader):
    """ 
    The ResourceLoader loads and cache resources from disk or network. 
    A Resource can be a 3D model, a texture, a sound, an URL etc...
    """
    
    def __init__(self):
        Loader.__init__(self, None)
        
    def loadModel(self, path, scale=1, pos=None, loaderOptions = None, 
                  noCache = None,allowInstance = False, callback = None, 
                  extraArgs = []):
        
        model = Loader.loadModel(self, path, loaderOptions, noCache, 
                                 allowInstance, callback, extraArgs)
        
        if model is not None:
            model.setScale(scale)
            
            if pos is not None:
                model.setPos(pos)
            
        return model
    
    def loadModelAndReparent(self, path, parentNode, scale=1, pos=None, 
                     loaderOptions = None, noCache = None,
                     allowInstance = False, callback = None, extraArgs = []):
        
        np = self.loadModel(path, scale, pos, loaderOptions, noCache, 
                            allowInstance, callback, extraArgs)
        np.reparentTo(parentNode)
        
        return np


class ModelNotFoundException(Exception):
    def __init__(self, modelPath):
        super(ModelNotFoundException, self).__init__("Model %s not found" % modelPath)
        
        
class KeyValueObject(object, DictMixin):
    """
    Instance attributes of this class can be accessed either using the dict
    notation or using the attribute notation.
    Ex. data = {"a":1,"b":{"x":1,"y":2}} ("b" must be a kvo too !)
    >> kvo = keyValueObject(data)
    >> kvo.a
    1
    >> kvo["b"[
    {"x":1,"y":2}
    >> kvo.b["x"] = 3
    >> kvo["b"].x
    3
    """
    def __init__(self, data):
        self.__dict__ = {}
        self.__dict__.update(data)
    
    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        self.__dict__[key] = value
    
    def __delitem__(self, item):
        del self.__dict__[item]
    
    def __str__(self):
        return self.__dict__.__str__()
    
    def keys(self):
        return self.__dict__.keys()
    
    def setPropertyFromKeyPath(self, keypath, newValue):
        tokens = keypath.split(".")
        if len(tokens) > 1:
            prev = self[tokens[0]]
            for token in tokens[1:]:
                if token == tokens[-1]:
                    prev[token] = newValue
                else:
                    prev = prev.get(token)
        else:
            self[keypath] = newValue

    
class GameEntity(KeyValueObject):
    """ 
    GameEntity is the class that represents an object in the game.
    An object can be animated, like a ball, static, like a tree or even 
    invisible, like a trigger.
    """
    def __init__(self, uid, data):
        super(GameEntity, self).__init__(data)
        self._uid = uid
        
    def __str__(self):
        return "%s (%d)" % (self.prettyName, self.UID)
    
    def update(self):
        if self.has_key("odephysics") and self.odephysics.has_key("geom"):
            # the position is updated by the physics manager
            pos = self.odephysics.geom.getPosition()
            self.render.nodepath.setPos(pos)
    
    def serialise(self):
        import copy
        
        attrs = copy.deepcopy(self)
        
        if self.has_key("render"): 
            if self.render.has_key("nodepath"):
                attrs["render"]["nodepath"] = None
            if self.render.has_key("parentNode"):
                # as the nodepath is unpicklable, I store the UID instead
                # however, if the parent node is one of the root nodes defined
                # only in the scene, as the UID is empty I get rid of the property
                # Maybe the root node in the scene should be entities too...
                uid = self.render.parentNode.getTag("UID")
                if uid == '':
                    del attrs["render"]["parentNode"]
                else:
                    attrs["render"]["parentNode"] = int(uid)
            if self.render.has_key("color"):
                # color is stored as a Vec4 which causes pickling problems so
                # I store it as a 4-elements tuple
                c = self.render.color
                attrs["render"]["color"] = (c[0], c[1], c[2], c[3]) 
                
        if self.has_key("odephysics"):
            if self.odephysics.has_key("geom"):
                attrs["odephysics"]["geom"] = None
            if self.odephysics.has_key("collisionBitMask"):
                attrs["odephysics"]["collisionBitMask"] = \
                    bitMaskToInt(self.odephysics.collisionBitMask)
            if self.odephysics.has_key("categoryBitMask"):
                attrs["odephysics"]["categoryBitMask"] = \
                    bitMaskToInt(self.odephysics.categoryBitMask)
                
        return attrs
        
        
    UID = property(fget=lambda self: self._uid, fset=None, fdel=None)
    nodepath = property(fget=lambda self: self.render.nodepath)
    

def transformToKeyValue(data, result={}):
    """ Given a dict returns the inner dicts converted to KeyValueObject(s)"""
    if type(data) is dict:
        for k,v in data.items():
            if type(v) is dict:
                kvo = KeyValueObject(v)
                result[k] = kvo
                transformToKeyValue(v, result[k])
            else:
                result[k] = v
    elif isinstance(data, KeyValueObject):
        return data
    else:
        raise TypeError("transformToKeyValue requires dict or KeyValueObject")
    return KeyValueObject(result)


previous_id = 0
class GameEntityManager(object):
    """
    This class creates and manage the objects used in the game. 
    Given a name, it creates a GameEntity instance with an unique id, it loads 
    the assets files using the ResourceLoader and initialise all the object 
    parameters using the other classes of the framework. For instance the 
    geometry is calculated by the Physics engine.
    """
    
    cache_size = 20
    
    def __init__(self):
        # assure there is only one instance of this class
        singleton(self)
        
        self._resourceLoader = ResourceLoader()
        
        self._cache = {}

    
    def createEntityFromNodepath(self, nodepath, params):
        """
        Create a new entity given the input params and an already existing
        nodepath. The priority will be given to nodepath properties.
        """
        logger.debug("Creating a new game entity from nodepath")
        
        data = transformToKeyValue(params, {})
        
        dataIsValid = True #self._sanityCheckData(data)
        
        ge = None
        if dataIsValid:
            uid = self.generateUID()
            if data.has_key("_uid"):
                uid = data._uid
            # ge has a custom class
            if data.has_key("python") and data.python.has_key("clazz"):
                ge = data.python.clazz(uid, data)
            else:
                ge = GameEntity(uid, data)
            
            # now apply only properties that are not written in the egg file
            if ge.render.has_key("scale"):
                nodepath.setScale(ge.render.scale)
                
            # add tags
            if ge.render.has_key("tags"):
                for tagName, tagValue in ge.render.tags.items():
                    nodepath.setTag(tagName, tagValue)
            else:
                # TODO iterate over tags and fill ge.render.tags
                pass
            
            # set the position to the one owned by the node
            ge.position.x = nodepath.getX()
            ge.position.y = nodepath.getY()
            ge.position.z = nodepath.getZ()
            
            # install UID tag, unfortunately must obligatory be a string
            nodepath.setTag("UID", str(ge.UID))
            
            # finally install the nodepath in the game object    
            ge.render.nodepath = nodepath
            
            if ge.has_key("odephysics") and ge.odephysics.has_key("geomType"):
                # replace bitmask numbers with appropriate objects
                catBitmask = BitMask32.bit(ge.odephysics.categoryBitMask)
                collBitmask = BitMask32.bit(ge.odephysics.collisionBitMask)
                ge.odephysics.categoryBitMask = catBitmask
                ge.odephysics.collisionBitMask = collBitmask
                
                # install geom property
                ge.odephysics.geom = POM.createGeomForObject(ge.odephysics, 
                                              ge.position, ge.render.nodepath)
                
            logger.debug("Game object %s succesfully created" % ge)
        else:
            logger.warning("Data was not valid, cannot create game object")
            if logger.isEnabledFor(DEBUG):
                logger.debug("Data was: %s", data)
                
        return ge
                
    
    def getEntity(self, params):
        """ 
        Create a new entity given the input data and the additional keyword
        arguments passed as parameters. Data must conform to the schema in
        the objects module.
        """

        # returns immediately if the entity is in the cache
        name = params["prettyName"]
        if name in self._cache:
            logger.debug("Cache hit for %s" % name)
            
            ge = self._cache[name] 
            if ge.render.nodepath.isEmpty():
                logger.debug("Cache invalid for %s, recreating object" % name)
            else:
                return self._cache[name]
        else:
            logger.debug("Cache miss for %s" % name)
            
        logger.debug("Creating game entity %s" % name)
        
        # The empty dictionary is VERY important as otherwise it will be
        # cached with all the previous values !
        data = transformToKeyValue(params, {})
        
        dataIsValid = True #self._sanityCheckData(data)
        
        ge = None
        if dataIsValid:
            # check uid existance. As parentNode is serialised as an ID to a
            # referring node, it is important to recreate the entity with the
            # same id as when it was serialised. 
            # FIXME Unfortunately this may cause UID collisions !!
            uid = self.generateUID()
            if data.has_key("_uid"):
                uid = data._uid
            # ge has a custom class
            if data.has_key("python") and data.python.has_key("clazz"):
                ge = data.python.clazz(uid, data)
            else:
                ge = GameEntity(uid, data)
            
            # setup nodepath
            if ge.render.has_key("modelPath"):
                nodepath = self._resourceLoader.loadModel(
                                        ge.render.modelPath, 
                                        ge.render.scale, 
                                        Point3(ge.position.x, 
                                               ge.position.y,
                                               ge.position.z))
            else:
                nodepath = NodePath(ge.prettyName)
                if ge.render.has_key("scale"):
                    nodepath.setScale(ge.render.scale)
                if ge.has_key("position"):
                    nodepath.setPos(Point3(ge.position.x,
                                               ge.position.y,
                                               ge.position.z))
                    rot = ge.position.rotation
                    # TODO
                    #nodepath.setQuat(Quat(rot[0],rot[1],rot[2],rot[3]))
            
            if ge.render.has_key("texture"):
                tex = self._resourceLoader.loadTexture(ge.render.texture)
                nodepath.setTexture(tex)
            
            # got color ?
            if ge.render.has_key("color"):
                # needs conversion from tuple to Vec4
                c = ge.render.color
                nodepath.setColor(Vec4(c[0], c[1], c[2], c[3]))
        
            # got material )
            if ge.render.has_key("material"):
                m = Material()
                m.setShininess(ge.render.material.shininess)
                m.setSpecular(ge.render.material.specular)
                
                nodepath.setMaterial(m,1)
                
            # add tags
            if ge.render.has_key("tags"):
                for tagName, tagValue in ge.render.tags.items():
                    nodepath.setTag(tagName, tagValue)
            else:
                ge.render.tags = {}
            
            # install UID tag, unfortunately must obligatory be a string
            nodepath.setTag("UID", str(ge.UID))
            
            # finally install the nodepath in the game object    
            ge.render.nodepath = nodepath
            
            # if geometry is enabled, I need to create a geometry and eventually
            # a body for the game object. The task is delegated to the Physic
            # Object Manager
            if ge.has_key("odephysics") and ge.odephysics.has_key("geomType"):
                # replace bitmask numbers with appropriate objects
                catBitmask = BitMask32.bit(ge.odephysics.categoryBitMask)
                collBitmask = BitMask32.bit(ge.odephysics.collisionBitMask)
                ge.odephysics.categoryBitMask = catBitmask
                ge.odephysics.collisionBitMask = collBitmask
                
                # install geom property
                ge.odephysics.geom = POM.createGeomForObject(ge.odephysics, \
                                                      ge.position, ge.nodepath)
                
            logger.debug("Game object %s succesfully created" % ge)
        else:
            logger.warning("Data was not valid, cannot create game object")
            if logger.isEnabledFor(DEBUG):
                logger.debug("Data was: %s", data)

        logger.debug("Caching entity: %s" % params["prettyName"])
        if len(self._cache) == self.cache_size:
            first = self._cache.keys()[0]
            logger.debug("Cache full, popping %s" % first)
            self._cache.pop(first)
        self._cache[params["prettyName"]] = ge
        
        return ge
            
    def generateUID(self):
        """ Generate a unique id for an object TODO improve me ... """
        global previous_id
        
        id = previous_id
        previous_id += 1
        
        return id
    
    def _sanityCheckData(self, data):
        isValid = True
        if data.has_key("python") and data.python.has_key("clazz"):
            isValid = isValid and isinstance(data.python.clazz, GameEntity)
        
        return isValid
    

GOM = GameEntityManager()
