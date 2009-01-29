# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import math, string

from random import randint 

colors = [Qt.white, Qt.green, Qt.red, Qt.yellow]

class Tile(object):
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.color = colors[randint(0, len(colors)-1)]
        
    def __str__(self):
        return "x: %s y: %s color: %s" % (self.x, self.y, self.color)

class TileEditorView(QWidget):
    
    TILES_NUM_X = 80
    TILES_NUM_Y = 80
    
    def __init__(self, parent=None):
        super(TileEditorView, self).__init__(parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                       QSizePolicy.Expanding))
        self.setMinimumSize(self.minimumSizeHint())
        
        self.selectedCellMousePos = None
        
        self.tiles = [[None for col in range(self.TILES_NUM_Y)] \
                      for row in range(self.TILES_NUM_X)]
    
    @pyqtSignature("")
    def onSaveMap(self):
        fileName = QFileDialog.getSaveFileName(self, "Save map")
        if fileName is not None:
            f = open(fileName, "w")
            for row in self.tiles:
                rowString = map(lambda x: str(x).join((str(x))), row)
                f.write(string.join(rowString))
            
            f.close()
      
    @pyqtSignature("")
    def loadMap(self):
        fileName = QFileDialog.getOpenFileName(self, "Map file (*.map)")
        if fileName is not None:
            f = open(fileName, "r")
            for idx, row in enumerate(f.readlines()):
                rowString = string.split(row)
                self.tiles[idx] = map(lambda x: int(x), rowString)
      
    def sizeHint(self):
        return QSize(1200, 1200)

    def minimumSizeHint(self):
        return QSize(1200, 1200)
    
    def updateSelection(self, x,y):
        tileWidth = float(self.width() / self.TILES_NUM_X)
        tileHeight = float(self.height() / self.TILES_NUM_Y)
        
        col = int(x / tileWidth)
        row = int(y / tileHeight)
        row = (self.TILES_NUM_Y -1) - row
        
        previous = self.tiles[row][col]
        if previous is not None:
            self.tiles[row][col] = None
        else:
            t = Tile(row, col, 1)
            self.tiles[row][col] = t
            
        self.update()
    
    def mousePressEvent(self, event):
        x = event.x()
        y = event.y()
        
        self.selectedCellMousePos = (x,y)
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
            for colIdx, cell in enumerate(row):
                if cell is not None:
                    painter.save()
                    painter.setPen(Qt.black)
                    painter.setBrush(QBrush(cell.color,Qt.SolidPattern))
                    x = colIdx * tileWidth
                    y = self.height()-tileHeight-rowIdx*tileHeight
                    painter.drawEllipse(x, y, tileWidth, tileHeight)
                    painter.restore()
        
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
        