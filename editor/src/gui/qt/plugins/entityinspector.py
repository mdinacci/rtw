# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("entity-inspector", DEBUG)

from mdlib.panda import event  
from mdlib.panda.entity import getPropertyType, getPropertyPath
from mdlib.types import Types


def dispatchEntityModifiedMessage(values):
    logger.debug("Dispatching message %s with values: %s" % \
                 (event.ENTITY_MODIFIED, values))
    messenger.send(event.ENTITY_PROPERTY_MODIFIED, values)

# Editors for the entity properties. Not the best OOP here...

class IntEditor(QSpinBox):
    def __init__(self, parent, keyPath, value, eid):
        super(IntEditor, self).__init__(parent)
        self.setSingleStep(1)
        self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.setValue(int(value))
        self.keyPath = keyPath
        self.eid = eid
        
        self.connect(self, SIGNAL("valueChanged(int)"), self.onValueChanged)
    
    def onValueChanged(self, value):
        dispatchEntityModifiedMessage([self.eid, self.keyPath, value])   
        
        
class StrEditor(QLineEdit):
    def __init__(self, parent, keyPath, value, eid):
        super(StrEditor, self).__init__(parent)
        self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.keyPath = keyPath
        self.setText(value)
        self.eid = eid
        
        #self.connect(self, SIGNAL("returnPressed()"), self.onValueChanged)
        self.connect(self, SIGNAL("editingFinished()"), self.onValueChanged)
    
    def onValueChanged(self):
        # for some reasons this method is called twice and I can't found
        # out the caller not even using the echo module. To workaround this
        # nuisance I explicitly set the modified flag to true once the message
        # has been dispatched. The method is still called twice but the message
        # is delivered only once
        if self.isModified():
            dispatchEntityModifiedMessage([self.eid, self.keyPath, 
                                           str(self.text())])   
            self.setModified(False)


class BoolEditor(QCheckBox):
    def __init__(self, parent, keyPath, value, eid):
        super(BoolEditor, self).__init__(parent)
        self.setText("True/False")
        self.keyPath = keyPath
        self.eid = eid
        
        self.connect(self, SIGNAL("stateChanged(int)"), self.onStateChanged)
        
        if value == 1:
            self.setChecked(True)
        else:
            self.setChecked(False)

    def onStateChanged(self, state):
        dispatchEntityModifiedMessage([self.eid, self.keyPath, state])
        
            
class FloatEditor(QDoubleSpinBox):
    def __init__(self, parent, keyPath, value, precision, eid):
        super(FloatEditor, self).__init__(parent)
        self.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.setDecimals(precision)
        self.setValue(float(value))
        self.setRange(-1000.0,1000.0)
        self.setSingleStep(0.5)
        self.keyPath = keyPath
        self.eid = eid
        
        step = float("0.%(#)s1" % {"#": "0"*(precision-1)})
        #self.setSingleStep(step)
        
        #self.connect(self, SIGNAL("editingFinished()"), self.onValueChanged)
        self.connect(self, SIGNAL("valueChanged(double)"), self.onValueChanged)
    
    def onValueChanged(self, value):
        dispatchEntityModifiedMessage([self.eid, self.keyPath, value])   
        self.setValue(value)


class EntityInspectorDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        # edit only in column 1
        if index.column() == 1:

            eid = index.model().getEntityIDForIndex(index)
            
            # for ex, if user clicked on the rotation value 
            # (normally (0,0,0,0)) this will return "rotation"
            key = str(index.sibling(index.row(), 0).data().toString())
            keyPath = getPropertyPath(key)
            propType = getPropertyType(keyPath)
            
            data = index.data().toString()
            
            if propType == int:
                return IntEditor(parent, keyPath, data, eid)
            elif propType == str:
                return StrEditor(parent, keyPath, data, eid)
            elif propType == bool:
                return BoolEditor(parent, keyPath, data, eid)
            elif propType == float:
                return FloatEditor(parent, keyPath, data, 6, eid)
            elif propType == Types.float1:
                return FloatEditor(parent, keyPath, data, 1, eid)
            elif propType == Types.float2:
                return FloatEditor(parent, keyPath, data, 2, eid)
            elif propType == Types.float2:
                return FloatEditor(parent, keyPath, data, 2, eid)
            else:
                return QItemDelegate.createEditor(self, parent, option, index)
            
            """
            elif propType == Types.tuple4:
                pass
            elif propType == Types.Geom:
                pass
            elif propType == Types.Color:
                pass
            """
            # find the type in the schema
            # provide an editor

class EntityInspector(QTreeView):
    
    def __init__(self, parent=None):
        super(EntityInspector, self).__init__(parent)
        
        self.setItemDelegate(EntityInspectorDelegate(self))
    
        
if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    ei = EntityInspector()
    ei.show()
    app.exec_()
    