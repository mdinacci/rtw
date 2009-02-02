# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import math, string

from random import randint 

__all__ = ['TileEditorModel', 'TileEditorController', 'TileEditorView', 'Mode',
           'Direction', 'Tile']

colors = [Qt.white, Qt.green, Qt.red, Qt.yellow, Qt.blue]

class Mode:
    DIRECTION = 0x1
    ELEVATION = 0x2

class Direction:
    FORWARD = 0x1
    BACKWARD = 0x2
    LEFT = 0x4
    RIGHT = 0x8


class Tile(object):
    def __init__(self, x, y, z, tileType, direction):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.type = int(tileType)
        self.direction = direction
        # TODO color will depend on type
        self.color = colors[randint(0,len(colors)-1)]
        
    def __repr__(self):
        return "x: %s y: %s z: %s type: %s" % (self.x, self.y, 
                                                self.z, self.type)

class TileEditorController(object):
    def __init__(self, view, model, defaultColor=None, defaultDirection=None):
        self.view = view
        self.model = model
        self.mode = Mode.DIRECTION
        if defaultColor is not None:
            self.currentColor = defaultColor
        else:
            self.currentColor = colors[randint(0,len(colors)-1)]
        if defaultDirection is not None:
            self.currentDirection = defaultDirection 
        else:
            self.currentDirection = Direction.FORWARD 
            
        
    def setCurrentColor(self, color):
        self.currentColor = color
        
    def setCurrentDirection(self, direction):
        self.currentDirection = direction
    
    def getCurrentColor(self):
        return self.currentColor
    
    def getCurrentDirection(self):
        return self.currentDirection
    
    def getMode(self):
        return self.mode

    def setMode(self, mode):
        self.mode = mode
        self.view.update()
        
    def getTiles(self):
        return self.model.tiles
    
    def addTileAt(self, tile, row, col):
        self.model.addTileAt(tile, row, col)
    
    def removeTileAt(self, row, col):
        self.model.removeTileAt(row, col)
    
    def tileAt(self, row, col):
        return self.model.tiles[row][col]
    
    def tilePressed(self, event):
        if self.mode == Mode.DIRECTION:
            self.view.updateSelection(event.x(),event.y())
        elif self.mode == Mode.ELEVATION:
            self.view.updateHeight(event)

    def mustAddTile(self):
        return self.mode == Mode.DIRECTION
    
    def mustPaintDirections(self):
        return self.mode == Mode.DIRECTION
    
    def mustPaintElevations(self):
        return self.mode == Mode.ELEVATION
    

class TileEditorModel(object):
    def __init__(self, xTiles, yTiles):
        self.xTiles = xTiles
        self.yTiles = yTiles
        self.reset(False)
        self.views = []
    
    def addView(self, view):
        self.views.append(view)
    
    def reset(self, updateView = True):
        tiles = [[None for col in range(self.yTiles)] \
                      for row in range(self.xTiles)]
        self.tiles = tiles
        if updateView:
            for view in self.views:
                view.update()
        
    def addTileAt(self, tile, row, col, updateView = True):
        self.tiles[row][col] = tile
        if updateView:
            for view in self.views:
                view.update()
        
    def removeTileAt(self, row, col, updateView = True):
        self.tiles[row][col] = None
        if updateView:
            for view in self.views:
                view.update()


class TileEditorView(QWidget):
    
    # must be here, and not in the model so I can set them using qt designer
    TILES_NUM_X = 80
    TILES_NUM_Y = 80
    
    def __init__(self, parent=None):
        super(TileEditorView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))
        self.setMinimumSize(self.minimumSizeHint())
        self.selectedCellMousePos = None

    def setController(self, controller):
        self.controller = controller
    
    
    def sizeHint(self):
        return QSize(1200, 1200)

    def minimumSizeHint(self):
        return QSize(1200, 1200)
    
    def getRowColAtPoint(self, x,y):
        tileWidth = float(self.width() / self.TILES_NUM_X)
        tileHeight = float(self.height() / self.TILES_NUM_Y)
        
        col = int(x / tileWidth)
        row = int(y / tileHeight)
        row = (self.TILES_NUM_Y -1) - row
        
        return (row,col)
    
    def updateHeight(self, event):
        def _updateHeight(x, y, zInc):
            row, col = self.getRowColAtPoint(x, y)
            tile = self.controller.tileAt(row,col)
            if tile is not None:
                # HACK the controller should do it
                tile.z+=zInc
                self.update()
        
        x = event.x()
        y = event.y()
        if event.modifiers() & Qt.ShiftModifier:
            _updateHeight(x,y,-1)
        else:
            _updateHeight(x,y,1)
                
    def updateSelection(self, x,y):
        row, col = self.getRowColAtPoint(x, y)
        previous = self.controller.tileAt(row,col)
        if previous is not None:
            self.controller.removeTileAt(row, col)
        else:
            color = self.controller.getCurrentColor()
            direction = self.controller.getCurrentDirection()
            t = Tile(col, row, 0, color, direction)
            self.controller.addTileAt(t, row, col)
    
    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        self.selectedCellMousePos = (x,y)
        
        self.controller.tilePressed(event)
        
    def mouseReleaseEvent(self, event):
        self.selectedCellMousePos = None
    
    def mouseMoveEvent(self, event):
        x,y = (event.x(), event.y())
        
        if self.controller.mustAddTile():
            pos = self.selectedCellMousePos
            if pos is not None:
                # check that mouse is outside cell boundaries otherwise I'll just 
                # deselect the selected cell
                tileWidth = float(self.width() / self.TILES_NUM_X)
                tileHeight = float(self.height() / self.TILES_NUM_Y)
                
                col = int(x / tileWidth)
                row = int(y / tileHeight)
                
                if row == int(pos[1]/tileHeight) and col == int(pos[0]/tileWidth):
                    event.ignore()
                else:
                    self.updateSelection(event.x(), event.y())
                    self.selectedCellMousePos = (x,y)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        tileWidth = float(self.width() / self.TILES_NUM_X)
        tileHeight = float(self.height() / self.TILES_NUM_Y)
        
        # draw grid 
        grid = []
        for i in range(self.TILES_NUM_X):
            x1 = x2 = i*tileHeight
            y1 = 0
            y2 = self.height()
            line = QLineF(x1,y1,x2,y2)
            grid.append(line)
            
        for i in range(self.TILES_NUM_Y):
            x1 = 0
            x2 = self.width()
            y1 = y2 = i*tileHeight
            line = QLineF(x1,y1,x2,y2)
            grid.append(line)
            
        painter.drawLines(grid)
        
        # draw tiles
        if hasattr(self, "controller"):
            tiles = self.controller.getTiles()
            for rowIdx, row in enumerate(tiles):
                for colIdx, tile in enumerate(row):
                    if tile is not None:
                        painter.save()
                        painter.setPen(tile.color)
                        
                        x = colIdx*tileWidth
                        y = self.height()-rowIdx*tileHeight
                        
                        if self.controller.mustPaintDirections():
                            # draw arrows
                            if tile.direction is Direction.FORWARD:
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y-1,
                                                 x+ tileWidth/2.0,
                                                 y-tileHeight+1)
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y-tileHeight+1,
                                                 x+ tileWidth/2.0-4,
                                                 y-8)
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y-tileHeight+1,
                                                 x+ tileWidth/2.0+4,
                                                 y-8)
                            elif tile.direction is Direction.BACKWARD:
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y-1,
                                                 x+ tileWidth/2.0,
                                                 y-tileHeight+1)
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y,
                                                 x+ tileWidth/2.0-4,
                                                 y-6)
                                painter.drawLine(x+ tileWidth/2.0,
                                                 y,
                                                 x+ tileWidth/2.0+4,
                                                 y-6)
                            elif tile.direction is Direction.LEFT:
                                startX = x+1
                                endX = x + tileWidth -1
                                painter.drawLine(startX, y-tileHeight/2.0,
                                                 endX, y-tileHeight/2.0)
                                painter.drawLine(startX,y-tileHeight/2.0,
                                                 startX+6,y-tileHeight+4)
                                painter.drawLine(startX,y-tileHeight/2.0,
                                                 startX+6,y-4)
                            elif tile.direction is Direction.RIGHT:
                                startX = x+1
                                endX = x + tileWidth -1
                                painter.drawLine(startX, y-tileHeight/2.0,
                                                 endX, y-tileHeight/2.0)
                                painter.drawLine(endX,y-tileHeight/2.0,
                                                 endX-6,y-tileHeight+4)
                                painter.drawLine(endX,y-tileHeight/2.0,
                                                 endX-6,y-4)
                                
                            
                        if self.controller.mustPaintElevations():
                            # draw elevations
                            painter.setPen(Qt.black)
                            painter.setBrush(QBrush(Qt.white,Qt.SolidPattern))
                            painter.drawText(x+tileWidth/2.0-3,y-2, "%s" \
                                             % int(tile.z))
                            
                        painter.restore()
        
    tilesNumX = pyqtProperty("int", lambda self: self.TILES_NUM_X, 
                         lambda self, x: setattr(self,"TILES_NUM_X", x), 
                         lambda self, x: setattr(self,"TILES_NUM_X", 10)) 
    tilesNumY = pyqtProperty("int", lambda self: self.TILES_NUM_Y, 
                             lambda self, y: setattr(self,"TILES_NUM_Y", y), 
                             lambda self, y: setattr(self,"TILES_NUM_Y", 10)) 

        
if __name__ == "__main__":
    import sys
    
    class TestDialog(QDialog):
        def __init__(self, parent=None):
            super(TestDialog, self).__init__(parent)
            layout = QBoxLayout(QBoxLayout.LeftToRight)
            
            scrollArea = QScrollArea()
            scrollArea.setWidget(TileEditorView())
            layout.addWidget(scrollArea)
            self.setLayout(layout)
    
    app = QApplication(sys.argv)
    test = TestDialog()
    test.show()
    app.exec_()
        