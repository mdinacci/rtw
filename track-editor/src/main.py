# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.autogen import *
from gui.qt.plugins.tileeditorview import *

from utils import *
from preview import TrackGenerator

import sys, string
from copy import deepcopy

import echo

class GUI(QMainWindow):
    def __init__(self, controller, *args):
        apply(QMainWindow.__init__, (self,) + args)
        self.controller = controller
        self._setupUi()
    
    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
            try:
                return self._mainWin.__dict__[attr]
            except KeyError, e:
                return self._tools.__dict__[attr]
      
    def _setupUi(self):
        self.setWindowTitle("Test")
        self.setGeometry(0,0,800,600)
        
        self._mainWin = Ui_MainWindow()
        self._mainWin.setupUi(self)
        
        # put the central widget in a layout. Qt Designer doesn't allow it :/
        layout = QBoxLayout(QBoxLayout.LeftToRight)
        layout.addWidget(self.tileEditorViewContainer)
        self.centralwidget.setLayout(layout)
        
        self._tools = Ui_toolsDock()
        toolsDock = QDockWidget("Tools", self)
        self._tools.setupUi(toolsDock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, toolsDock)
        
        # directions
        self.connect(self._tools.actionForward, \
                 SIGNAL("toggled(bool)"),self.controller.toggleDirectionForward)
        self.connect(self._tools.actionBackward, \
                 SIGNAL("toggled(bool)"),self.controller.toggleDirectionBackward)
        self.connect(self._tools.actionLeft, \
                     SIGNAL("toggled(bool)"),self.controller.toggleDirectionLeft)
        self.connect(self._tools.actionRight, \
                     SIGNAL("toggled(bool)"),self.controller.toggleDirectionRight)
        
        # colors
        
        
        # toolbar
        self.connect(self._mainWin.actionNew, SIGNAL("triggered()"),\
                     self.controller.newTrack)
        self.connect(self._mainWin.actionOpen, SIGNAL("triggered()"),\
                     self.controller.openTrack)
        self.connect(self._mainWin.actionSave, SIGNAL("triggered()"),\
                     self.controller.saveTrack)
        self.connect(self._mainWin.actionQuit, SIGNAL("triggered()"),\
                     self.controller.quit)
        self.connect(self._mainWin.actionPreview, SIGNAL("triggered()"),\
                     self.controller.previewTrack)
        
        # mode
        self.connect(self._mainWin.actionDirectionMode, 
                     SIGNAL("triggered()"), self.controller.toggleModeDirection)
        self.connect(self._mainWin.actionElevationMode, 
                     SIGNAL("triggered()"), self.controller.toggleModeElevation)
        

class TrackEditor(object):

    SEPARATOR = '!'
    
    def __init__(self, argv):
        self.app = QApplication(argv)
        self.gui = GUI(self)
        self.trackGenerator = TrackGenerator()
        
        self.tileView = self.gui.tileEditorView
        self.tileModel = TileEditorModel(TileEditorView.TILES_NUM_X,
                                         TileEditorView.TILES_NUM_Y)
        self.tileController = TileEditorController(self.tileView,
                                           self.tileModel,
                                           defaultDirection=Direction.FORWARD)
        self.tileView.setController(self.tileController)
        self.tileModel.addView(self.tileView)
        
        self._prevDirAction = self.gui.actionForward
        
    def newTrack(self):
        self.tileModel.reset()
    
    def openTrack(self):
        # TODO ask to save current track
        self.tileModel.reset()
        fileName = QFileDialog.getOpenFileName(self, "Map file (*.map)")
        if fileName != '':
            f = open(fileName)
            for i,row in enumerate(f.readlines()):
                cells = row.split(self.SEPARATOR)
                j = 0
                for cell in cells:
                    if cell != "\n":
                        if cell.startswith("N"):
                            # assign empty tiles
                            numNones = int(cell[1:])
                            for none in range(numNones):
                                self.tileModel.addTileAt(None, i, j+none, False)
                            # a bit of a hack the minus one, but it's necessary
                            # since j is increased at the end of the loop
                            j += numNones-1
                        else:
                            p= string.split(cell)
                            tile = Tile(p[0],p[1],p[2],p[3], 0x1)
                            self.tileModel.addTileAt(tile, i, j, False)
                    j +=1
            f.close()
            
            self.tileView.update()
    
    def saveTrack(self):
        fileName = QFileDialog.getSaveFileName(self, "Save map (*.map)")
        if fileName is not None:
            if fileName != '':
                f = open(fileName, "w")
                tiles = self.tileModel.tiles
                for row in tiles:
                    leftNonesWritten = rightNonesWritten = False
                    nones = 0
                    for tile in row:
                        # keep track of the number of empty tiles
                        if tile is None:
                            nones +=1
                        else:
                            if leftNonesWritten is False:
                                # ex. write N30- if there are 30 consecutives
                                # empty tiles 
                                f.write("N%d%s" % (nones, self.SEPARATOR))
                                nones = 0
                                leftNonesWritten = True
                            f.write("%f %f %f %d%s" % (tile.x, tile.y, tile.z, 
                                                       tile.type, 
                                                       self.SEPARATOR))
                    if nones > 0: 
                        # write right empty tiles number
                        f.write("N%d%s" % (nones, self.SEPARATOR))
                    f.write("\n")
                f.close()
    
    def quit(self):
        # TODO ask to save track
        sys.exit(1)

    def toggleDirectionForward(self, toggled):
        if not self.tileController.getCurrentDirection() == Direction.FORWARD:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionForward
            self.tileController.setCurrentDirection(Direction.FORWARD)
    
    def toggleDirectionBackward(self, toggled):
        if not self.tileController.getCurrentDirection() == Direction.BACKWARD:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionBackward
            self.tileController.setCurrentDirection(Direction.BACKWARD)
    
    def toggleDirectionLeft(self, toggled):
        if not self.tileController.getCurrentDirection() == Direction.LEFT:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionLeft
            self.tileController.setCurrentDirection(Direction.LEFT)
    
    def toggleDirectionRight(self, toggled):
        if not self.tileController.getCurrentDirection() == Direction.RIGHT:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionRight
            self.tileController.setCurrentDirection(Direction.RIGHT)

    def toggleModeElevation(self):
        self.gui.actionDirectionMode.toggle()
        self.tileController.setMode(Mode.ELEVATION)

    def toggleModeDirection(self): 
        self.gui.actionElevationMode.toggle()
        self.tileController.setMode(Mode.DIRECTION)
    
    def previewTrack(self):
        tiles = self.tileModel.tiles
        self.trackGenerator.generate(tiles)
        self.trackGenerator.showTrack()
        
    def run(self):
        self.gui.show()
        self.app.exec_()
        
if __name__ == '__main__':
    TrackEditor(sys.argv).run()
    
