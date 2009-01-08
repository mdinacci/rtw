# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

class SceneManager(object):
    """
    This class is used by the application class to save and 
    restore a scene. It can export/load:
    - entities
        - geometry
        - physics
        - other attributes
    """
    
    def load(self, fromFile):
        pass
    
    def save(self, toFile):
        pass
