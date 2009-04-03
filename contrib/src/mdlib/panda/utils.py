# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Some utilities
"""

from pandac.PandaModules import Quat, Point3, Vec4
from direct.directtools.DirectGeometry import LineNodePath

def pointAtZ(z, point, vec):
    """ Given a line (vector plus origin point) and a desired z value,
    returns the point on the line where the desired z value is what we want. 
    This is how we know where to position an object in 3D space based on a
    2D mouse position. It also assumes that we are dragging in the XY plane.
    
    This is derived from the mathematical of a plane, solved for a given point
    
    Author: taken from panda3D examples
    """
    return point + vec * ((z-point.getZ()) / vec.getZ())


def vec4ToQuat(vec4):
    """ Convert a 4 elements tuple to a Quaternion """ 
    return Quat(vec4[0],vec4[1],vec4[2],vec4[3])


def showTrimeshLines(geom, parentNode, thickness=3.0, 
                     colorVec=Vec4(1,1,0,1)):
        lines = LineNodePath(parent=parentNode, thickness=thickness, 
                             colorVec = colorVec)
        lines.reset()
        for i in xrange(geom.getNumTriangles()):
            a = Point3(0)
            b = Point3(0)
            c = Point3(0)
            geom.getTriangle( i, a, b, c )
            l = (
                  (a.getX(), a.getY(), a.getZ()),\
                  (b.getX(), b.getY(), b.getZ()),\
                  (c.getX(), c.getY(), c.getZ()),\
                  (a.getX(), a.getY(), a.getZ())
                )
            lines.drawLines([l])
        
        lines.create()


def showGeometryLines(entity, parentNode, thickness=3.0, 
                      colorVec=Vec4(1,0,0,1), zOffset=0.0):
    """ Displays lines around the bounding box of a physic object """
    
    p1 = Point3(0,0,0)
    p2 = Point3(0,0,0)
    p1,p2 = entity.getTightBounds()
    
    p1.setZ(p1.getZ() + zOffset)
    p2.setZ(p2.getZ() + zOffset)
    
    lines = LineNodePath(parent = parentNode, thickness = thickness, 
                         colorVec = colorVec)
    
    lines.reset()
    
    # lower rectangle
    l1 = (
          (p1.getX(), p1.getY(), p1.getZ()),
          (p2.getX(), p1.getY(), p1.getZ()),
          (p2.getX(), p2.getY(), p1.getZ()),
          (p1.getX(), p2.getY(), p1.getZ()),
          (p1.getX(), p1.getY(), p1.getZ()),
          )
    lines.drawLines([l1])
    
    # upper rectangle
    l2 = (
          (p1.getX(), p1.getY(), p2.getZ()),
          (p2.getX(), p1.getY(), p2.getZ()),
          (p2.getX(), p2.getY(), p2.getZ()),
          (p1.getX(), p2.getY(), p2.getZ()),
          (p1.getX(), p1.getY(), p2.getZ()),
          )
    lines.drawLines([l2])
    
    # junctions
    l3 = zip(l1,l2)
    lines.drawLines(l3)
    
    lines.create()
    
    return lines


