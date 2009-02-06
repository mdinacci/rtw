# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MVCLCDNumber(QLCDNumber):
    def __init__(self, parent=None):
        super(MVCLCDNumber, self).__init__(parent)
        self.setSegmentStyle(QLCDNumber.Flat)
    
    def setModel(self, model):
        self.model = model
    
    def update(self):
        self.display(self.model.getTileCount())
