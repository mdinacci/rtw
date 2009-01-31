# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import math, string

from random import randint 

colors = [Qt.white, Qt.green, Qt.red, Qt.yellow, Qt.blue]

class Tile(object):
    def __init__(self, x, y, z, tileType):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.type = int(tileType)
        # TODO color will depend on type
        self.color = colors[randint(0,len(colors)-1)]
        
    def __repr__(self):
        return "x: %s y: %s z: %s type: %s" % (self.x, self.y, 
                                                self.z, self.type)

class TileEditorView(QWidget):
    
    TILES_NUM_X = 80
    TILES_NUM_Y = 80
    
    SEPARATOR = '!'
    
    def __init__(self, parent=None):
        super(TileEditorView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))
        self.setMinimumSize(self.minimumSizeHint())
        
        self.selectedCellMousePos = None
        
        self.tiles = self.reset()
    
    def reset(self):
        return [[None for col in range(self.TILES_NUM_Y)] \
                      for row in range(self.TILES_NUM_X)]
    
    
    
    @pyqtSignature("")
    def on_actionQuit_triggered(self):
        pass
        
    @pyqtSignature("")
    def on_actionNew_triggered(self):
        # TODO ask to save
        self.tiles = self.reset()
        self.update()
        
    @pyqtSignature("")
    def on_actionSave_triggered(self):
        fileName = QFileDialog.getSaveFileName(self, "Save map (*.map)")
        if fileName is not None:
            if fileName != '':
                f = open(fileName, "w")
                for row in self.tiles:
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
      
    @pyqtSignature("")
    def on_actionLoad_triggered(self):
        self.tiles = self.reset()
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
                                self.tiles[i][j+none] = None
                            # a bit of a hack the minus one, but it's necessary
                            # since j is increased at the end of the loop
                            j += numNones-1
                        else:
                            p= string.split(cell)
                            self.tiles[i][j] = Tile(p[0],p[1],p[2],p[3])
                    j +=1
            f.close()
            self.update()
                    
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
    
    def updateHeight(self, x, y, zInc):
        row, col = self.getRowColAtPoint(x, y)
        tile = self.tiles[row][col]
        if tile is not None:
            tile.z+=zInc
            self.update()
    
    def updateSelection(self, x,y):
        row, col = self.getRowColAtPoint(x, y)
        previous = self.tiles[row][col]
        if previous is not None:
            self.tiles[row][col] = None
        else:
            t = Tile(col, row, 0, colors[randint(0, len(colors)-1)])
            self.tiles[row][col] = t
            
        self.update()
    
    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        self.selectedCellMousePos = (x,y)

        if event.modifiers() & Qt.ShiftModifier:
            self.updateHeight(x,y,1)
        elif event.modifiers() & Qt.ControlModifier:
            self.updateHeight(x,y,-1)
        else:
            self.updateSelection(x,y)
        
    def mouseReleaseEvent(self, event):
        self.selectedCellMousePos = None
    
    def mouseMoveEvent(self, event):
        x,y = (event.x(), event.y())
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
    
    def keyPressEvent(self, event):
        pass
    
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
        for rowIdx, row in enumerate(self.tiles):
            for colIdx, tile in enumerate(row):
                if tile is not None:
                    painter.save()
                    painter.setPen(Qt.black)
                    #color = colors[randint(0,len(colors)-1)]
                    painter.setBrush(QBrush(tile.color,Qt.SolidPattern))
                    x = colIdx * tileWidth
                    y = self.height()-tileHeight-rowIdx*tileHeight
                    painter.drawEllipse(x, y, tileWidth, tileHeight)
                    painter.setBrush(QBrush(Qt.white,Qt.SolidPattern))
                    # magic numbers are offsets to place the number at the 
                    # center of the square
                    painter.drawText(x+tileWidth/2 -3,y+tileHeight-2, "%s" \
                                     % int(tile.z))
                    painter.restore()
        
        tileNumX = pyqtProperty("int", lambda self: self.TILES_NUM_X, 
                             lambda self, x: setattr(self,"TILES_NUM_X", x), 
                             lambda self, x: setattr(self,"TILES_NUM_X", 10)) 
        tileNumY = pyqtProperty("int", lambda self: self.TILES_NUM_Y, 
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
        