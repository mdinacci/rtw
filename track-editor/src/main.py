# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.autogen import *

import sys, string
from copy import deepcopy

from preview import TrackGenerator

class GUI(QMainWindow):
    def __init__(self, controller, *args):
        apply(QMainWindow.__init__, (self,) + args)
        self.controller = controller
        self._setupUi()
        
    def getTiles(self):
        return self.tileEditorView.tiles
        
    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self._mainWin.__dict__[attr]
         
    def _setupUi(self):
        self.setWindowTitle("Test")
        self.setGeometry(0,0,800,600)
        
        self._mainWin = Ui_MainWindow()
        self._mainWin.setupUi(self)
        
        self.connect(self._mainWin.actionPreview, SIGNAL("triggered()"),\
                     self.controller.previewTrack)
        

class TrackEditor(object):
    def __init__(self, argv):
        self.app = QApplication(argv)
        self.gui = GUI(self)
        self.trackGenerator = TrackGenerator()
        
    def previewTrack(self):
        # I need to work on a new copy because the generation may require
        # the creation of new control points, which is done by adding new tiles
        # to the rows. These tiles may not be representable on the editor, as 
        # they have fractionary coordinates.
        tiles = deepcopy(self.gui.getTiles())
        self.trackGenerator.generate(tiles)
        self.trackGenerator.showTrack()
        
    def run(self):
        self.gui.show()
        self.app.exec_()
        
        
if __name__ == '__main__':
    TrackEditor(sys.argv).run()
    
