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

class EntityItemModel(QStandardItemModel):
    def __init__(self, *args):
        apply(QStandardItemModel.__init__, (self,) + args)
        
        # the purpose of this map is to store the QStandardItem for each 
        # entity added to the model. This is for easier data retrieval, however
        # if an entity is deleted I have to remember also to remove the entry 
        # from this dictionary
        self.entityItemMap = {}
        
    def getIndexForEntityID(self, eid):
        logger.debug("Returning index for entity ID: %s" % eid)
        return self.entityItemMap[int(eid)].index()
    
    def getEntityIDForIndex(self, index):
        sibling = index.sibling(index.row(), 0)
        parent = sibling.parent()
        
        recursion = 10
        while recursion > 0:
            parentItem = parent.model().itemFromIndex(parent)
            recursion -= 1
            for entity, item in self.entityItemMap.items():
                if item is parentItem:
                    return entity
            # item not found, go to parent'parent
            parent = parent.parent()
    

class SceneGraphModel(EntityItemModel):
    """ Model class for the SceneGraphView widget """
    
    def __init__(self, *args):
        super(SceneGraphModel, self).__init__(*args)
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
                    self.entityItemMap[int(rootNode.getNetTag("UID"))] = item 
                    _populateTree(child, item)
                else:
                    item = EntityItem(child.getName())
                    parent.appendRow(item)
                    self.entityItemMap[int(rootNode.getNetTag("UID"))] = item 
            
        if rootNode is not None:
            self.entityItemMap = {}
            logger.debug("Populating scene graph model")
            self.clear()
            parent = self.invisibleRootItem();
            rootItem = QStandardItem(rootNode.getName())
            parent.appendRow(rootItem)
            self.entityItemMap[rootNode.getNetTag("UID")] = rootItem 
            _populateTree(rootNode, rootItem)  
            

class EntityItem(QStandardItem):
    def __init__(self, data, parent=None):
        super(EntityItem, self).__init__(data)
        self.parentItem = parent
        self.itemData = data
    
    def __str__(self):
        return self.itemData
        #return self.itemData.prettyName
    

class EntityInspectorModel(EntityItemModel):
    def __init__(self, *args):
        super(EntityInspectorModel, self).__init__(*args)

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

        if len(entities) > 0:
            logger.debug("Populating entity inspector model")
    
            self.clear()
            self.entityItemMap = {}
            
            parent = self.invisibleRootItem();
            rootItem = QStandardItem("Entities")
            parent.appendRow([rootItem, QStandardItem("")])
            for entity in entities:
                item = QStandardItem(entity.prettyName)
                rootItem.appendRow([item, QStandardItem("#%d"%entity.UID)])
                _populateEntity(entity, item)
                self.entityItemMap[entity.UID] = item 
            
