# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("entity", DEBUG)

from mdlib.panda.input import SafeDirectObject
from mdlib.panda.data import GOM, GameEntity, EntityType, \
        KeyValueObject, transformToKeyValue
from mdlib.panda import event
from mdlib.types import Types

from pandac.PandaModules import NodePath, Point3, OdeGeom

class Track(GameEntity):
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
    
    def __init__(self, uid, data):
        """
        I need the previous cell and the number of cells, no need to store
        the cells here, let's delegate it to the GOM
        """
        super(Track, self).__init__(uid, data)
        
        # keep a list of cells here for easier management
        self._cells = []
        
        self._subscribeToEvents()
        
        
    def createRow(self):
        rowID = len(self._cells)/self.physics.rowWidth +1
        logger.debug("Creating row #%d" % rowID)
        # TODO port row to GameEntity
        rp = row_params.copy()
        rp["render"]["parentNode"] = self.render.nodepath
        row = GOM.createEntity(rp)
        #rowNode = self.render.nodepath.attachNewNode("row-%d" % rowID)
        
        yield row
        
        for i in range(0, row.physics.width):
            yield self._createCell(row.render.nodepath)
    
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
        params = cell_params.copy()
        
        # some shortcuts
        render = params["render"]
        render["parentNode"] = parent
        physics = params["physics"]
        
        if len(self._cells) > 0:
            prevPos = self._cells[-1].position
            if len(self._cells) % self.physics.rowWidth == 0: 
                incX = - (self.physics.rowWidth-1) * physics["length"]
                incY = physics["length"]
            else:
                incX = physics["length"]
                incY = 0
            pos = Point3(prevPos.x + incX, prevPos.y+ incY, prevPos.z)
        else:
            pos = Point3(0,0,1)
        
        # set row, column tag; it makes easy to identify the cell after
        row = (len(self._cells)) / (self.physics.rowWidth)
        col = (len(self._cells)) % (self.physics.rowWidth)
        
        params["position"]["x"] = pos.getX()
        params["position"]["y"] = pos.getY() 
        params["position"]["z"] = pos.getZ() 
        
        render["color"] = Types.Color.b_n_w[len(self._cells) % 2]
        render["tags"]["pos"] = "%d %d" % (row, col)
        
        cell = GOM.createEntity(params)
        
        logger.debug("Created cell #%d at row,col,pos (%d,%d,%s)" 
                     % (len(self._cells),row,col,pos))
        self._cells.append(cell)
        
        return cell
    
    def serialise(self):
        attrs = super(Track, self).serialise()
        del attrs._cells
        return attrs

    
class TrackCell(GameEntity):
    """ This entity represents a 3D cell in a track """
    
    def __init__(self, uid, data):
        super(TrackCell, self).__init__(uid, data)
        
    def __str__(self):
        return "Cell #%s at %s" % (self.UID, self.render.nodepath.getTag("pos"))

    
# Property schema: defines the existing properties and their type
property_schema = {
                 "archetype": str,
                 "prettyName": str,
                 "python": 
                    {
                     "clazz": object
                     },
                 "position":
                    { 
                     "x": float,
                     "y": float,
                     "z": float,
                     "rotation": Types.tuple4
                     },
                 "physics": 
                    {
                     "collisionBitMask": int, # unsigned
                     "categoryBitMask" : int, # unsigned
                     "geomType": Types.Geom,
                     "geom": OdeGeom,
                     "radius": Types.float2,
                     "hasBody": bool,
                     "linearSpeed": int,
                     "density":int,
                     "xForce" : Types.float1,
                     "yForce" : Types.float1,
                     "zForce" : Types.float1,
                     "torque" : Types.float1,
                     "length": Types.float2,
                     "width": Types.float2,
                     "height": Types.float2,
                     },
                 "render": 
                    {
                     "entityType": int, # EntityType constant
                     "color": Types.Color,
                     "nodepath": NodePath,
                     "scale": int,
                     "modelPath": str,
                     "parentNode": NodePath,
                     "isDirty": bool,
                     "tags": {}
                     }
                }

ball_params = {
               "archetype": "Player",
               "prettyName": "Ball",
               "position": 
                    { 
                     "x": 4,
                     "y": 2,
                     "z": 50,
                     "rotation": (0,0,0,0)
                     },
               "physics": 
                    {
                     "collisionBitMask": 0x00000001,
                     "categoryBitMask" : 0x00000001,
                     "geomType": Types.Geom.SPHERE_GEOM_TYPE,
                     "radius":  0.56,
                     "hasBody": True,
                     "linearSpeed": 3000,
                     "density":500,
                     "xForce" : 0,
                     "yForce" : 0,
                     "zForce" : 0,
                     "torque" : 0
                     },
               "render": 
                    {
                     "entityType": EntityType.ACTOR,
                     "scale": 1,
                     "modelPath": "golf-ball",
                     "isDirty": True,
                     }
               }

# default parameters for the cell objects
cell_params = {
               "archetype": "Tracks/Cells",
               "prettyName": "Cell",
               "python":
                    {
                     "clazz": TrackCell
                     },
               "position":
                    {
                     "x": 0,
                     "y": 0,
                     "z": 1,
                     "rotation": (0,0,0,0)
                     },
               "physics": 
                    {
                     "collisionBitMask": 0x00000001,
                     "categoryBitMask" : 0x00000000,
                     "geomType": Types.Geom.BOX_GEOM_TYPE,
                     "length": 2.0,
                     "width": 2.0,
                     "height": 0.2,
                     "hasBody": False
                     },
               "render": 
                    {
                     "entityType": EntityType.ACTOR,
                     "scale": 1,
                     "modelPath": "cell_normal",
                     "isDirty": True,
                     "color": None,
                     "tags" : {"pos":None}
                     }
               }

row_params = {
              "archetype":"Tracks/Rows",
              "prettyName": "Row",
              "render": #necessary even if empty in order to create a NodePath
                {
                 # HACK should be NONE but row won't be displayed othw
                 "entityType": EntityType.NONE 
                },
              "physics":
                {
                 "width":5
                 }
              }

track_params = {
                "archetype": "Tracks",
                "prettyName": "Track",
                "python": 
                    {
                     "clazz": Track
                     },
                "render": #necessary even if empty in order to create a NodePath
                    {
                     # HACK should be NONE but TrackCell won't be displayed othw
                     "entityType": EntityType.ACTOR 
                     },
                "physics":
                    {
                     "rowWidth": 5
                     }
                }

environment_params = {
                      "archetype": "Background",
                      "prettyName": "Environment",
                      "position":
                            {
                             "x": -10,
                             "y": 35,
                             "z": -5,
                             "rotation": (0,0,0,0)
                             },
                      "render": 
                            {
                             "entityType": EntityType.BACKGROUND,
                             "scale": 0.25,
                             "modelPath": "environment",
                             "isDirty": True,
                             }
                     }

# create a global KeyValueObject to simplify the getPropertyType function 
schema_kvo = transformToKeyValue(property_schema)

def getPropertyType(propPath, schema=property_schema):
    if propPath is not None:
        expression = "schema_kvo.%s" % propPath
        return eval(expression)

def getPropertyPath(propName, schema=property_schema, result=""):
    """ Returns the type of a property given its name (the name is unique) """
    for key, value in schema.items():
        if key == propName:
            result += propName
            return result
        elif type(value) is dict:
            s = getPropertyPath(propName, value)
            if s is not None:
                result+= "%s.%s" % (key,s)
                return result
