# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from PyQt4 import QtGui, QtDesigner
from tileeditorview import TileEditorView

class TileEditorViewPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
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
        return TileEditorView(parent)

    def name(self):
        return "TileEditorView"
    
    def group(self):
        return "Game editor"

    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False
    
    def domXml(self):
        return '<widget class="TileEditorView" name=\"tileEditorView\" />\n'
    
    def includeFile(self):
        return "tileeditorview"
