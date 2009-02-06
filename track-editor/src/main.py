# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("track-editor", DEBUG)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.autogen import *
from gui.qt.plugins.tileeditorview import *

from preview import TrackGenerator

import sys, string, cPickle
from copy import deepcopy
from subprocess import Popen

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
        
        # types
        self.connect(self._tools.actionNeutral, \
                 SIGNAL("toggled(bool)"),self.controller.toggleNeutralType)
        self.connect(self._tools.actionJump, \
                 SIGNAL("toggled(bool)"),self.controller.toggleJumpType)
        self.connect(self._tools.actionSlow, \
                 SIGNAL("toggled(bool)"),self.controller.toggleSlowType)
        self.connect(self._tools.actionSpeed, \
                 SIGNAL("toggled(bool)"),self.controller.toggleSpeedType)
        self.connect(self._tools.actionInvert, \
                 SIGNAL("toggled(bool)"),self.controller.toggleInvertType)
        self.connect(self._tools.actionBounceBack, \
                 SIGNAL("toggled(bool)"),self.controller.toggleBounceBackType)
        
        # toolbar
        self.connect(self._mainWin.actionNew, SIGNAL("triggered()"),\
                     self.controller.newTrack)
        self.connect(self._mainWin.actionOpen, SIGNAL("triggered()"),\
                     self.controller.openTrack)
        self.connect(self._mainWin.actionSave, SIGNAL("triggered()"),\
                     self.controller.saveTrack)
        self.connect(self._mainWin.actionQuit, SIGNAL("triggered()"),\
                     self.controller.quit)
        self.connect(self._mainWin.actionExport, SIGNAL("triggered()"),\
                     self.controller.exportTrack)
        self.connect(self._mainWin.actionPreview, SIGNAL("triggered()"),\
                     self.controller.previewTrack)
        
        # mode
        self.connect(self._mainWin.actionDirectionMode, 
                     SIGNAL("triggered()"), self.controller.toggleModeDirection)
        self.connect(self._mainWin.actionElevationMode, 
                     SIGNAL("triggered()"), self.controller.toggleModeElevation)
        

class TrackEditor(object):

    SEPARATOR = '!'
    EXPORT_CMD = 'egg-qtess -cs z-up -tbnauto -up 5 -o %s %s'
    TEMP_FILE = '/tmp/test.egg'
    
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
        self.tileModel.addView(self.gui.mvcLcdNumber)
        
        self.gui.mvcLcdNumber.setModel(self.tileModel)
        
        self._prevDirAction = self.gui.actionForward
        self._prevDirType = self.gui.actionNeutral
    
    def exportTrack(self):
        fileName = QFileDialog.getSaveFileName(self.gui, "Save track (*.egg)")
        if fileName != '':
            # TODO to launch in a new thread, progress bar etc...
            self.trackGenerator.generate(self.tileModel.tiles)
            # FIXME functionality should be here but for the moment I leave it 
            # in the track generator in order to save from the preview
            self.trackGenerator.saveTo(self.TEMP_FILE)
            # run egg-qtess
            cmd= self.EXPORT_CMD % (fileName, self.TEMP_FILE)
            Popen(cmd.split())
            logger.info("Track succesfully exported to %s" % fileName)
        
    
    def newTrack(self):
        self.tileModel.reset()
    
    def saveTrack(self):
        fileName = QFileDialog.getSaveFileName(self.gui, "Save map (*.map)")
        if fileName != '':
            f = open(fileName, "wb")
            tiles = self.tileModel.tiles
            cPickle.dump(tiles, f)
    
    def openTrack(self):
        self.tileModel.reset()
        fileName = QFileDialog.getOpenFileName(self.gui, "Map file (*.map)")
        if fileName != '':
            f = open(fileName, "rb")
            tiles = cPickle.load(f)
            self.tileModel.tiles = tiles
            self.tileView.update()
            
    def quit(self):
        # TODO ask to save track
        sys.exit(1)
        
    def previewTrack(self):
        tiles = self.tileModel.tiles
        self.trackGenerator.generate(tiles)
        self.trackGenerator.showTrack()
        
    def toggleNeutralType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.NEUTRAL:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionNeutral
            self.tileController.currentType = TileType.NEUTRAL
    
    def toggleJumpType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.JUMP:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionJump
            self.tileController.currentType = TileType.JUMP
    
    def toggleSpeedType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.SPEED:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionSpeed
            self.tileController.currentType = TileType.SPEED
    
    def toggleSlowType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.SLOW:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionSlow
            self.tileController.currentType = TileType.SLOW
    
    def toggleInvertType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.INVERT:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionInvert
            self.tileController.currentType = TileType.INVERT
    
    def toggleBounceBackType(self, toggled):
        if not self.tileController.getCurrentType() == TileType.BOUNCE_BACK:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionBounceBack
            self.tileController.currentType = TileType.BOUNCE_BACK

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
    
    def run(self):
        self.gui.show()
        self.app.exec_()

if __name__ == '__main__':
    TrackEditor(sys.argv).run()
    
