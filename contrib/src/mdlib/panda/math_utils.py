# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Some math utilities
"""

from pandac.PandaModules import Quat

def vec4ToQuat(vec4):
    """ Convert a 4 elements tuple to a Quaternion """ 
    return Quat(vec4[0],vec4[1],vec4[2],vec4[3])