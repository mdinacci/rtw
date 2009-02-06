# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import NodePath, SheetNode, NurbsSurfaceEvaluator, \
    EggNurbsSurface, EggVertex, EggData, EggVertexPool, EggGroup
from pandac.PandaModules import VBase3, Point3, Point4D, VBase4

from pandac.PandaModules import BamFile, Filename

class Sheet(NodePath):
    """ This class defines a NURBS surface whose control vertices are
    defined based on points relative to one or more nodes in space, so
    that the "sheet" will animate as the nodes move around.  It uses
    the C++ SheetNode class to achieve fancy rendering effects like
    thick lines built from triangle strips. """
    
    showSheet = base.config.GetBool('show-sheet', 1)

    def __init__(self, name="sheet"):
        self.sheetNode = SheetNode(name)
        self.surface = NurbsSurfaceEvaluator()
        self.sheetNode.setSurface(self.surface)
        self.sheetNode.setUseVertexColor(True)
        NodePath.__init__(self, self.sheetNode)
        
        self.name = name
        
    def setup(self, uOrder, vOrder, uVertsNum, verts, uKnots=None, vKnots=None):
        """This must be called to define the shape of the surface initially, 
        and may be called again as needed to adjust the surface's properties.

        uOrder and vOrder must be either 1, 2, 3, or 4, and is one more than the
        degree of the surface; most NURBS surfaces are order 4.
        
        uVertsNum is the number of vertices on the u axis. The number of 
        vertices on the v axis is therefore given by the equation:
        
        vVertsNum = len(self.verts) / self.uVertsNum 
        
        verts is a list of (NodePath, point) tuples, defining the control 
        vertices of the curve.  For each control vertex, the NodePath may refer 
        to an arbitrary node in the scene graph, indicating the point should be 
        interpreted in the coordinate space of that node (and it will 
        automatically move when the node is moved), or it may be the empty 
        NodePath or None to indicate the point should be interpreted in the 
        coordinate space of the Sheet itself.  
        
        Each point value may be either a 3-tuple or a 4-tuple 
        (or a VBase3 or VBase4). If it is a 3-component vector, it represents a 
        3-d point in space; a 4-component vector represents a point in 4-d 
        homogeneous space; that is to say, a 3-d point and an additional weight
        factor (which should have been multiplied into the x y z
        components).

        verts may be a list of dictionaries instead of a list of tuples.  
        In this case, each vertex dictionary may have any of the following 
        elements:

          'node' : the NodePath indicating the coordinate space
          'point' : the 3-D point relative to the node; default (0, 0, 0)
          'color' : the color of the vertex, default (1, 1, 1, 1)

        In order to enable the per-vertex color, you must call 
        sheet.sheetNode.setPerVertexColor().

        uKnots and vKnots are optional.  If specified, they should be a list of
        monotonically increasing floats, and should be of length len(verts) + 
        order.  If they're omitted, a default knot string is generated that 
        consists of the first (order - 1) and last (order - 1) values the same, 
        and the intermediate values incrementing by 1.
        """

        self.uOrder = uOrder
        self.vOrder = vOrder
        self.verts = verts
        
        self.uVertsNum =  uVertsNum
        self.vVertsNum = len(self.verts) / self.uVertsNum
        
        self.uKnots = uKnots
        self.vKnots = vKnots
        
        self.recompute()
    
    
    def recompute(self):
        """Recomputes the surface after its properties have changed.
        Normally it is not necessary for the user to call this
        directly."""
        
        if not self.showSheet:
            return
        
        numVerts = len(self.verts)
        self.surface.reset(self.uVertsNum, self.vVertsNum)
        self.surface.setUOrder(self.uOrder)
        self.surface.setVOrder(self.vOrder)

        defaultNodePath = None
        defaultPoint = (0, 0, 0)
        defaultColor = (1, 1, 1, 1)

        useVertexColor = self.sheetNode.getUseVertexColor()
        # this function exists for ropeNode but not for sheetNode ?
        vcd = 0 #self.sheetNode.getVertexColorDimension()
        
        idx = 0
        for v in range(self.vVertsNum):
            for u in range(self.uVertsNum):
                vertex = self.verts[idx]
                if isinstance(vertex, tuple):
                    nodePath, point = vertex
                    color = defaultColor
                else:
                    nodePath = vertex.get('node', defaultNodePath)
                    point = vertex.get('point', defaultPoint)
                    color = vertex.get('color', defaultColor)
                    
                if isinstance(point, tuple):
                    # force all points to float
                    point = map(lambda x: float(x), point)
                    if (len(point) >= 4):
                        self.surface.setVertex(u, v, \
                                    VBase4(point[0], point[1], point[2], point[3]))
                    else:
                        self.surface.setVertex(u, v, \
                                               VBase3(point[0], point[1], point[2]))
                else:
                    self.surface.setVertex(u, v, point)
                if nodePath:
                    self.surface.setVertexSpace(u, v, nodePath)
                if useVertexColor:
                    self.surface.setExtendedVertex(u, v, vcd + 0, color[0])
                    self.surface.setExtendedVertex(u, v, vcd + 1, color[1])
                    self.surface.setExtendedVertex(u, v, vcd + 2, color[2])
                    self.surface.setExtendedVertex(u, v, vcd + 3, color[3])
                idx +=1
        
        if self.uKnots != None:
            for i in range(len(self.uKnots)):
                self.surface.setUKnot(i, self.uKnots[i])
        
        if self.vKnots != None:
            for i in range(len(self.vKnots)):
                self.surface.setVKnot(i, self.vKnots[i])
        
        self.sheetNode.resetBound(self)
        
        
    def normalize(self, uKnots = True, vKnots = True):
        """ Normalize the surface """
        if uKnots:
            self.surface.normalizeUKnots()
        if vKnots:
            self.surface.normalizeVKnots()
        
        
    def getPoints(self, length, coordSpace=None):
        """Returns a list of length points, evenly distributed in
        parametric space on the sheet, in the coordinate space passed as 
        second parameter. If no second parameter is passed the coordinate space
        will be that of the sheet itself """
        
        if coordSpace is None: coordSpace = self
        result = self.surface.evaluate(coordSpace)
        numPts = length
        sheetPts = []
        for i in range(numPts):
            pt = Point3()
            u = v = i / float(numPts -1)
            result.evalPoint(u,v, pt)
            sheetPts.append(pt)
        return sheetPts

    
    def toEgg(self, coordSpace=None):
        """ Convert this Sheet to an EggNurbsSurface and return it"""
        
        egg = EggData()
        pool = EggVertexPool("sheet_vertex_pool")
        egg.addChild(pool)
        
        group = EggGroup('sheet_group')
        egg.addChild(group) 
        
        ens = EggNurbsSurface(self.getName())
        ens.setup(self.uOrder, self.vOrder, 
                  self.surface.getNumUKnots(), 
                  self.surface.getNumVKnots())
        ens.setUSubdiv(self.uVertsNum)
        ens.setVSubdiv(self.vVertsNum)
        group.addChild(ens)
        
        for vert in self.verts:
            vertex = EggVertex()
            
            point = vert['point']
            p = Point4D(point[0], point[1], point[2], 1.0)
            vertex.setPos4(p)
            
            # generated file won't load with color informations !
            #color = vert['color']
            #vertex.setColor(VBase4(color[0], color[1], color[2], color[3]))
            
            pool.addVertex(vertex)
            ens.addVertex(vertex)
            
        return egg
