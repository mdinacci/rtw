# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("widgets", DEBUG)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from mdlib.panda.data import KeyValueObject

class SceneGraphModel(QStandardItemModel):
    """ Model class for the SceneGraphView widget """
    
    def __init__(self, *args):
        apply(QStandardItemModel.__init__, (self,) + args)
        self.setHorizontalHeaderLabels(['Entity'])
        self._headerLabels = {0:"Node"}
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole: 
            return QVariant(self._headerLabels[section])
        
        return QVariant()
    
    
    def populate(self, rootNode):
        def _populateTree(rootNode, parent):
            children = rootNode.getChildren().asList()
            for child in children:
                # if child has children recursively add them to the tree
                if child.getNumChildren() > 0:
                    item = QStandardItem(child.getName())
                    parent.appendRow(item)
                    _populateTree(child, item)
                else:
                    parent.appendRow(QStandardItem(child.getName()))
            
        if rootNode is not None:
            logger.debug("Populating scene graph browser")
            self.clear()
            parent = self.invisibleRootItem();
            rootItem = QStandardItem(rootNode.getName())
            parent.appendRow(rootItem)
            _populateTree(rootNode, rootItem)  
            

class EntityItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0
    
    def __str__(self):
        return self.itemData.prettyName
    

class EntityInspectorModel(QStandardItemModel):
    def __init__(self, *args):
        apply(QStandardItemModel.__init__, (self,) + args)
        self.entities = []
        self._headerLabels = {0:"Entity", 1: "Value"}
        self.setColumnCount(2)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole: 
            return QVariant(self._headerLabels[section])
        
        return QVariant()
    
    def populate(self, entities):
        def _populateEntity(props, parent):
            for k,v in props.items():
                item = QStandardItem(k)
                if isinstance(v, KeyValueObject):
                    parent.appendRow([item, QStandardItem("")])
                    _populateEntity(v, item)
                else:
                    parent.appendRow([item, QStandardItem(str(v))])
                
        logger.debug("Populating entity inspector")

        self.entities = entities
        self.clear()
        
        parent = self.invisibleRootItem();
        rootItem = QStandardItem("Entities")
        parent.appendRow([rootItem, QStandardItem("")])
        for entity in self.entities:
            item = QStandardItem(entity.prettyName)
            rootItem.appendRow([item, QStandardItem("")])
            _populateEntity(entity, item)
        
