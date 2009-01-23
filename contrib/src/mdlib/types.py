# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# extension classes used for properties
class Types:
    class tuple3(tuple): pass # a tuple with three elements
    class tuple4(tuple): pass # a tuple with four elements
    class float1(float): pass # a float with single decimal precision
    class float2(float): pass # a float with double decimal precision
    
    class Geom:
        BOX_GEOM_TYPE = 0x1
        SPHERE_GEOM_TYPE = 0x2
        
    class Color(object):
        """ Some color constants """
        # some colors
        BLACK = (0,0,0,1)
        WHITE = (1,1,1,1)
        RED = (1,0,0,1)
        GREEN = (0,1,0,1)
        BLUE = (0,0,1,1)
        HIGHLIGHT = (1,1,0.3,0.5)
        
        COLOR_IDX = 0
        b_n_w = [BLACK,WHITE]

