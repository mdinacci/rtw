# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from PyQt4 import QtGui, QtDesigner
from scenegraphview import SceneGraphView

class SceneGraphViewPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        QtDesigner.QPyDesignerCustomWidgetPlugin.__init__(self)
        
        self.initialized = False
        
    def initialize(self, core):
        if self.initialized:
            return
        
        self.initialized = True
        
    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        return SceneGraphView(parent)

    def name(self):
        return "SceneGraphView"
    
    def group(self):
        return "Game editor"

    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False
    
    def domXml(self):
        return '<widget class="SceneGraphView" name=\"sceneGraphView\" />\n'
    
    def includeFile(self):
        return "scenegraphview"
