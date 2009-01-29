# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Some math utilities
"""

from pandac.PandaModules import Quat

def pointAtZ(z, point, vec):
    """ Given a line (vector plus origin point) and a desired z value,
    returns the point on the line where the desired z value is what we want. 
    This is how we know where to position an object in 3D space based on a
    2D mouse position. It also assumes that we are dragging in the XY plane.
    
    This is derived from the mathematical of a plane, solved for a given point
    """
    return point + vec * ((z-point.getZ()) / vec.getZ())

def vec4ToQuat(vec4):
    """ Convert a 4 elements tuple to a Quaternion """ 
    return Quat(vec4[0],vec4[1],vec4[2],vec4[3])