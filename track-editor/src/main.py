# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("track-editor", DEBUG)

from mdlib.panda import tools

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.autogen import *
from gui.qt.plugins.tileeditorview import *

from preview import TrackGenerator

import sys, string, cPickle, time, os
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
        
        for i in range(5,0,-1): self._tools.tileSizeBox.addItem("%s"%i)
        self._tools.tileSizeBox.setCurrentIndex(1)
        self._tools.tileSizeBox.setCurrentIndex(0)
        
        self.connect(self._tools.tileSizeBox, 
                 SIGNAL("currentIndexChanged (const QString&)"), 
                 self.controller.tileSizeChanged)
        
        # directions
        self.connect(self._tools.actionForward, \
                 SIGNAL("toggled(bool)"),self.controller.toggleDirectionForward)
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
    TEMP_FILE = '/tmp/test.egg'
    QTESS_FILE = '/tmp/qtess.egg'
    MAP_FORMAT_VERSION = "1.1"
    TESSELLATION_CURVES = 5
    
    def __init__(self, argv):
        self.app = QApplication(argv)
        self.gui = GUI(self)
        
        self.tileView = self.gui.tileEditorView
        self.tileModel = TileEditorModel(self.tileView.tilesNumX, 
                                         self.tileView.tilesNumY)
        self.tileController = TileEditorController(self.tileView,
                                           self.tileModel,
                                           defaultDirection=Direction.FORWARD)
        self.tileView.setController(self.tileController)
        self.tileModel.addView(self.tileView)
        self.tileModel.addView(self.gui.mvcLcdNumber)
        
        self.gui.mvcLcdNumber.setModel(self.tileModel)
        
        self._prevDirAction = self.gui.actionForward
        self._prevDirType = self.gui.actionNeutral
        
        self.trackGenerator = TrackGenerator(self.tileView.tilesNumX)
        self._currentTrack = None
    
    def exportTrack(self):
        fileName = QFileDialog.getSaveFileName(self.gui, "Save track (*.egg)")
        if fileName != '':
            # TODO to launch in a new thread, progress bar etc...
            self.trackGenerator.generate(self.tileModel.tiles)
            # FIXME the egg should be written here but for the moment I leave it 
            # in the track generator in order to save from the preview
            self.trackGenerator.saveTo(self.TEMP_FILE)
            # tessellate
            tools.tessellate(self.TEMP_FILE, self.QTESS_FILE, 
                         self.TESSELLATION_CURVES, self.trackGenerator.rowCount)
            
            # sleep in order to give egg-qtess some time to run
            while not os.path.exists(self.QTESS_FILE):
                time.sleep(0.2)
            
            # organize the polygons in rows
            tools.groupify(self.QTESS_FILE, self.TEMP_FILE)
            
            # get rid of holes
            tools.holeify(self.TEMP_FILE, fileName, 
                          self.tileModel.getHoleIndexes())
            
            logger.info("Track succesfully exported to %s" % fileName)
        
    
    def newTrack(self):
        self.tileModel.reset()
    
    
    def saveTrack(self):
        def _saveTrack(fileName, tiles, version):
            logger.info("Saving track as %s" % fileName)
            f = open(fileName, "wb")
            cPickle.dump(version, f, -1)
            cPickle.dump(tiles, f, -1)
            
        if self._currentTrack is None:
            fileName = QFileDialog.getSaveFileName(self.gui, "Save map (*.map)")
            if fileName != '':
                self._currentTrack = fileName
                _saveTrack(self._currentTrack, self.tileModel.tiles, \
                           self.MAP_FORMAT_VERSION)
        else:
            _saveTrack(self._currentTrack, self.tileModel.tiles, \
                       self.MAP_FORMAT_VERSION)
            
            
    
    def openTrack(self):
        self.tileModel.reset()
        fileName = QFileDialog.getOpenFileName(self.gui, "Map file (*.map)")
        if fileName != '':
            logger.info("Opening track %s" % fileName)
            f = open(fileName, "rb")
            version = cPickle.load(f)
            if version == self.MAP_FORMAT_VERSION:
                tiles = cPickle.load(f)
                self.tileModel.tiles = tiles
                self.tileView.update()
                self._currentTrack = fileName
            else:
                QErrorMessage().showMessage("Map with format version %s \
                are not supported" % version)
            
    def quit(self):
        # TODO ask to save track
        sys.exit(1)
        
    def previewTrack(self):
        tiles = self.tileModel.tiles
        self.trackGenerator.generate(tiles)
        self.trackGenerator.showTrack()
        
    def tileSizeChanged(self, size):    
        s = str(size)
        logger.info("Tile size changed to %s", s)
        self.tileController.currentTileSize = int(s)
        
    def toggleNeutralType(self, toggled):
        if not self.tileController.currentType == TileType.NEUTRAL:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionNeutral
            self.tileController.currentType = TileType.NEUTRAL
    
    def toggleJumpType(self, toggled):
        if not self.tileController.currentType == TileType.JUMP:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionJump
            self.tileController.currentType = TileType.JUMP
    
    def toggleSpeedType(self, toggled):
        if not self.tileController.currentType == TileType.SPEED:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionSpeed
            self.tileController.currentType = TileType.SPEED
    
    def toggleSlowType(self, toggled):
        if not self.tileController.currentType == TileType.SLOW:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionSlow
            self.tileController.currentType = TileType.SLOW
    
    def toggleInvertType(self, toggled):
        if not self.tileController.currentType == TileType.INVERT:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionInvert
            self.tileController.currentType = TileType.INVERT
    
    def toggleBounceBackType(self, toggled):
        if not self.tileController.currentType == TileType.HOLE:
            self._prevDirType.toggle()
            self._prevDirType = self.gui.actionBounceBack
            self.tileController.currentType = TileType.HOLE

    def toggleDirectionForward(self, toggled):
        if not self.tileController.currentDirection == Direction.FORWARD:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionForward
            self.tileController.setCurrentDirection(Direction.FORWARD)
    
    def toggleDirectionBackward(self, toggled):
        if not self.tileController.currentDirection == Direction.BACKWARD:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionBackward
            self.tileController.setCurrentDirection(Direction.BACKWARD)
    
    def toggleDirectionLeft(self, toggled):
        if not self.tileController.currentDirection == Direction.LEFT:
            self._prevDirAction.toggle()
            self._prevDirAction = self.gui.actionLeft
            self.tileController.setCurrentDirection(Direction.LEFT)
    
    def toggleDirectionRight(self, toggled):
        if not self.tileController.currentDirection == Direction.RIGHT:
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
    
