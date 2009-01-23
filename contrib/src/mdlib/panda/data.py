# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("data", DEBUG)

from mdlib.patterns import singleton
from mdlib.panda.physics import POM 

from pandac.PandaModules import Point3, Quat, BitMask32, Vec4
from pandac.PandaModules import NodePath, Filename, LoaderOptions
from direct.showbase.Loader import PandaLoader
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


class EntityType:
    NONE  = 0x0   # non renderable objects (triggers, lights, cameras etc..)
    STATIC = 0x1  # environments and level geometry
    ACTOR = 0x2   # things that have a physic geometry and eventually a body
    BACKGROUND = 0x3 # the background "behind" everything
    ALPHA = 0x4   # alpha objects

    
class ResourceLoader(object):
    """ 
    The ResourceLoader loads and cache resources from disk or network. 
    A Resource can be a 3D model, a texture, a sound, an URL etc...
    """
    def __init__(self):
        self.loader = PandaLoader()
        
    def loadModel(self, path, scale, pos):
        """ SYNCHRONOUSLY load a model from disk """
        node = self.loader.loadSync(Filename(path), LoaderOptions())
        if node != None:
            model = NodePath(node)
        else:
            raise ModelNotFoundException()
        model.setScale(scale)
        model.setPos(pos)
        
        return model
    
    def loadModelAndReparent(self, path, scale, pos, parentNode):
        self.loadModel(path, scale, pos).reparentTo(parentNode)


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
        if self.has_key("physics") and self.physics.has_key("geom"):
            # the position is updated by the physics manager
            pos = self.physics.geom.getPosition()
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
                
        if self.has_key("physics"):
            if self.physics.has_key("geom"):
                attrs["physics"]["geom"] = None
            if self.physics.has_key("collisionBitMask"):
                attrs["physics"]["collisionBitMask"] = \
                    bitMaskToInt(self.physics.collisionBitMask)
            if self.physics.has_key("categoryBitMask"):
                attrs["physics"]["categoryBitMask"] = \
                    bitMaskToInt(self.physics.categoryBitMask)
                
        return attrs
        
        
    UID = property(fget=lambda self: self._uid, fset=None, fdel=None)
    

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
    def __init__(self):
        # assure there is only one instance of this class
        singleton(self)
        
        self._resourceLoader = ResourceLoader()

    
    def createEntity(self, params):
        """ 
        Create a new entity given the input data and the additional keyword
        arguments passed as parameters. Data must conform to the schema in
        the objects module.
        """
        logger.debug("Creating a new game entity")
        
        # TODO transform data to a dict of KeyValue objects
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
            uid = None
            if data.has_key("_uid"):
                uid = data._uid
            else: 
                uid = self._generateUID()
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
            
            
            # NOTE: attaching the node to the parent node is delegated to the 
            # scene as there may not be enough informations here (gettin entity 
            # from UID) to succesfully bind the entity to its parent.         
            
            # reparent node if parentNode is set
            #if ge.render.has_key("parentNode") \
            #                    and ge.render.parentNode is not None: 
            #    if type(ge.render.parentNode) is type: # a nodepath 
            #        nodepath.reparentTo(ge.render.parentNode)
            
            # got color ?
            if ge.render.has_key("color"):
                # needs conversion from tuple to Vec4
                c = ge.render.color
                nodepath.setColor(Vec4(c[0], c[1], c[2], c[3]))
                
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
            if ge.has_key("physics") and ge.physics.has_key("geomType"):
                # replace bitmask numbers with appropriate objects
                catBitmask = BitMask32.bit(ge.physics.categoryBitMask)
                collBitmask = BitMask32.bit(ge.physics.collisionBitMask)
                ge.physics.categoryBitMask = catBitmask
                ge.physics.collisionBitMask = collBitmask
                
                # install geom property
                ge.physics.geom = POM.createGeomForObject(ge.physics, ge.position)
                
                #a = Point3(0,0,0); b = Point3(0,0,0); ge.physics.geom.getAABB(a,b)
                #displayLines(a,b, go)
                
            logger.debug("Game object %s succesfully created" % ge)
        else:
            logger.warning("Data was not valid, cannot create game object")
            if logger.isEnabledFor(DEBUG):
                logger.debug("Data was: %s", data)
                
        return ge
            
    def _generateUID(self):
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
