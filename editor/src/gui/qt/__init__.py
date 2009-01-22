# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG
logger = ConsoleLogger("gui", DEBUG)

from pandac.PandaModules import WindowProperties

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from model import *
from autogenerated import *

class EditorGUI(QMainWindow):
    def __init__(self, controller, *args):
        logger.debug("Initialising GUI")
        
        apply(QMainWindow.__init__, (self,) + args)
        
        self._controller = controller
        self._pandaWindow = None
        
        self._setupUi()
        self._setupConnections()
        
        # set up idle callback to give p3D some time to run
        timer =  QTimer(self)
        self.connect(timer, SIGNAL("timeout()"), controller.idleCallback)
        timer.start(0)
        
        logger.debug("GUI initialised")

    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self._mainWin.__dict__[attr]

    def _setupUi(self):
        # import autogenerated window code 
        self._mainWin = Ui_MainWindow()
        self._mainWin.setupUi(self)

        # import autogenerated scene graph dock widget code
        self._sgvUi = Ui_sceneGraphDock()
        self._sgvDockWidget = QDockWidget("Scene Graph View", self)
        self._sgvUi.setupUi(self._sgvDockWidget)
        self.sceneGraphView = self._sgvUi.sceneGraphView
        
        # import autogenerated entity inspector dock widget code
        self._eiUi = Ui_EntityInspectorDock()
        self._eiDockWidget = QDockWidget("Entity Inspector", self)
        self._eiUi.setupUi(self._eiDockWidget)
        self.entityInspector = self._eiUi.entityInspector
        
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._sgvDockWidget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._eiDockWidget)
        
        self.centralwidget.resizeEvent = self.resizeP3DWindow
    
    def _setupConnections(self):
        tools = ("newButton","openButton","saveButton","copyButton",
                 "pasteButton","deleteButton","undoButton","redoButton")
        
        for tool in tools:
            s = "self._controller.on%sClicked" % (tool[0].capitalize()+tool[1:])
            self.connect(getattr(self,tool), SIGNAL("triggered()"), eval(s))
            
    
    def getHandle(self):
        return self._mainWin.p3dContainer.window().winId()
    
    def getLoadedFile(self):
        return QFileDialog.getOpenFileName(self, "Scene file (*.rtw)")
        
    def getSaveFile(self):
        return QFileDialog.getSaveFileName(self, "Save scene file")

    def setPandaWindow(self, pandaWindow):
        """ Set the panda window (base.win) """
        self._pandaWindow = pandaWindow

        # </ok>
    def onModelUpdate(self):
        pass
        #self._mainWin.sceneGraphView.setModel(self._controller.getSceneGraphModel())
        #self._mainWin.sceneGraphView.expandAll()
        #self._entityChoice.populate()
    
    def showEntityProperties(self, props):
        """ Show the properties of an entity in the property grid """
        pass
    
    def resizeP3DWindow(self, event):
        size = event.size()
        logger.debug("Resizing panda window to %s-%s" % (size.width(), size.height()))
        # at app startup pandaWindow is not set yet
        if self._pandaWindow != None:
            pandaWin = self
            pandaWin = self._mainWin.p3dContainer
            w,h = size.width(), size.height()
            wp = WindowProperties()
            
            # FIXME detect widget position wrt parent
            wp.setOrigin(1, 56)
            
            minW = pandaWin.minimumWidth()
            minH = pandaWin.minimumHeight()
            
            if w < minW:
                w = minW
            if h < minH:
                h = minH
            
            wp.setSize(w, h)
            self._pandaWindow.requestProperties(wp)
        
            # FIXME doesnt' work
            messenger.send('window-event',[self._pandaWindow])
        
        self.update()
        