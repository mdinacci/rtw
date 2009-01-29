# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from PyQt4 import QtGui, QtDesigner
from assetbrowser import AssetBrowser

class AssetBrowserPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
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
        return AssetBrowser(parent)

    def name(self):
        return "AssetBrowser"
    
    def group(self):
        return "Game editor"

    def toolTip(self):
        return ""

    def whatsThis(self):
        return ""

    def isContainer(self):
        return False
    
    def domXml(self):
        return '<widget class="AssetBrowser" name=\"assetBrowser\" />\n'
    
    def includeFile(self):
        return "assetbrowser"
