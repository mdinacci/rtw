# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from mdlib.gui.qt import ImageLabel

import os

class AssetsRepository(object):
    
    VALID_EXTENSIONS = ("jpg","png","gif")
    
    def __init__(self, root):
        self.root = root
        self.name = root
        self.assets = []
        self.populate(root)
        
    def populate(self, root):
        self.assets=[os.path.join(root,asset) for asset in os.listdir(root) \
                     if self.isAsset(asset)]
        
    def isAsset(self, asset):
        isasset = False
        if "." in asset:
            extension = asset[asset.index(".")+1:]
            isasset = extension.lower() in self.VALID_EXTENSIONS
        
        return isasset
    
    def __len__(self):
        return len(self.assets)
    
    def __iter__(self):
        return self.assets.__iter__()
    

class AssetsBrowserModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super(AssetsBrowserModel, self).__init__(parent)
        self.repos = []
    
    def rowCount(self, index=QModelIndex()):
        return 2

    def columnCount(self, index=QModelIndex()):
        return 2

    def data(self, index, role):
        return QVariant("/home/mdinacci/Photos/2009/01/01/img_6991.jpg")
    
    def getRepositories(self):
        for repo in self.repos:
            yield repo
            
    def addRepository(self, repo):
        self.repos.append(repo)
        self.showRepository(repo)
        self.view.populate(self.repos)
        
    def removeRepository(self, repo):
        self.repos.remove(repo)
        self.view.populate(self.repos)

    def hideRepository(self, repo):
        repo.isVisible = False
    
    def showRepository(self, repo):
        repo.isVisible = True
        

class AssetsBrowserItemDelegate(QItemDelegate):
    def paint(self, painter, option, index):
        #img = index.model().data()
        img = "/home/mdinacci/Photos/2009/01/01/img_6991.jpg"
        pixmap = QPixmap(img)
        pixmap = pixmap.scaled(self.size, self.flags)
        
        painter.save()
        rect = QRect(option.rect.x(), option.rect.y(), 48,48)
        painter.drawPixmap(rect,pixmap)
        painter.restore()
        

class AssetsBrowser(QTableView):
    """ Follows the Autonomous View architecture however the model is 
    separate """
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.setWindowTitle("Assets Browser")
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        delegate = AssetsBrowserItemDelegate(self)
        delegate.size = QSize(64,64)
        delegate.flags = Qt.KeepAspectRatioByExpanding
        self.setItemDelegate(delegate)
        
        self.setShowGrid(False)
    
    def sizeHint(self):
        return QSize(300, 250)

    def minimumSizeHint(self):
        return QSize(300, 250)
    
    def chooseNewRepository(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setWindowTitle("Select a directory containing assets")
        
        dirName = ""
        if dialog.exec_():
            dirName= dialog.selectedFiles()[0];
            
        return dirName

    def removeRepository(self, set):
        # TODO remove pics corresponding to set
        pass

    def __init__(self, view):
        self.view = view
        self.model = AssetsBrowserModel(view)
        
    def addRepository(self):
        dirName = str(self.view.chooseNewRepository())
        if dirName is not None:
            if os.path.isdir(dirName):
                repo = AssetsRepository(dirName)
                self.model.addRepository(repo)
                
    def removeRepository(self):
        # get selected set from list
        set = None
        self.model.removeRepository(set)


if __name__ == '__main__':
    repos = [["/home/mdinacci/Photos/2009/01/01/img_6991.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6993.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6990.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6992.jpg"],
              ["/home/mdinacci/Photos/2009/01/01/img_6991.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6993.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6990.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6992.jpg"],
              ["/home/mdinacci/Photos/2009/01/01/img_6991.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6993.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6990.jpg",
              "/home/mdinacci/Photos/2009/01/01/img_6992.jpg"]]
    
    import sys
    app = QApplication(sys.argv)
    
    win = QMainWindow()
    
    ab = QTableView()
    ab.setShowGrid(False)
    ab.horizontalHeader().hide()
    ab.verticalHeader().hide()
    ab.resizeColumnsToContents()
    ab.setColumnWidth(0,50)
    ab.setRowHeight(0,50)
    delegate = AssetsBrowserItemDelegate(ab)
    delegate.size = QSize(48,48)
    delegate.flags = Qt.KeepAspectRatioByExpanding
    ab.setItemDelegate(delegate)
    ab.setModel(AssetsBrowserModel(win))
    
    win.setCentralWidget(ab)
    win.show()
    app.exec_()
    