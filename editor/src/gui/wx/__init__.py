# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import WindowProperties

import sys
from os import getcwd

import wx
from wx import xrc

from widgets import PropertyGrid, SceneGraphTree, EntitySelectionChoice

fileWildcard = "Scene file (*.rtw) |*.rtw| "

class EditorGUI(wx.App):
    
    def __init__(self, xrcFile, controller):
        self._xrcFile = xrcFile
        self._controller = controller
        self._pandaWindow = None
        wx.App.__init__(self)

    def getId(self, name):
        return xrc.XRCID(self.frame, name)
        
    def getWidget(self, name):
        return xrc.XRCCTRL(self.frame, name)
  
    def _openDialog(self, msg, dlgStyle):
        dlg = wx.FileDialog(
            self.frame, message=msg, defaultDir=getcwd(), 
            defaultFile="scene.rtw", wildcard=fileWildcard, 
            style=dlgStyle
            )
        
        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        
        dlg.Destroy()
        
        return path
        
    
    def getLoadedFile(self):
        return self._openDialog("Load file...", wx.OPEN | wx.CHANGE_DIR)
        
    def getSaveFile(self):
        return self._openDialog("Save file as...", wx.SAVE)
  
    def showEntityProperties(self, props):
        """ Show the properties of an entity in the property grid """
        self.propertyGrid.reset(len(props),2)
        for key,val in props.items():
            self.propertyGrid.addProperty(key, type(val), val)
    
    def setPandaWindow(self, pandaWindow):
        """ Set the panda window (base.win) """
        self._pandaWindow = pandaWindow
        self.onSize()
        
    def onModelUpdate(self):
        self._sgTree.populate()
        self._entityChoice.populate()
    
    def OnInit(self):
        self.res = xrc.XmlResource(self._xrcFile)
        self.frame = self.res.LoadFrame(None, 'mainFrame')
        
        self.SetTopWindow(self.frame)
        self.frame.CenterOnScreen()
        self.frame.Show()
        
        self.surfaceHandle=self.frame.GetHandle()
        self.evtLoop = wx.EventLoop()
        self.oldLoop = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(self.evtLoop)
        
        self._initWidgets()
        self._bindEvents()
        
        # start wx window
        self.MainLoop()
        
        return True
    
    def onPandaPanelEnter(self, e):
        print "ENTERING"
        
    def onPandaPanelLeave(self,e ):
        print "LEAVING"
    
    def onSize(self, event=None):
        # at app startup pandaWindow is not set yet
        if self._pandaWindow != None:
            pandaWin = xrc.XRCCTRL(self.frame, "PandaPanel")
            w,h = pandaWin.GetSizeTuple()
            wp = WindowProperties()
            wp.setOrigin(0, 0)
            
            minW = pandaWin.GetMinWidth()
            minH = pandaWin.GetMinHeight()
            
            if w < minW:
                w = minW
            if h < minH:
                h = minH
            
            wp.setSize(w, h)
            self._pandaWindow.requestProperties(wp)
        
            # FIXME doesnt' work
            messenger.send('window-event',[self._pandaWindow])
        
        if event <> None: event.Skip()
    
    def onQuit(self, event):
        self.frame.Destroy()
        while self.evtLoop.Pending():
            self.evtLoop.Dispatch()
        
        self._controller.onShutDown()
    
    def _initWidgets(self):
        # Init splitter sizes as it's not supported in XRC (...)
        w,h = self.frame.GetSizeTuple()
        self._pandaSplitWin = self.getWidget("PandaSplitterWindow")
        self._pandaSplitWin.SetSashPosition(w)
        self._pandaSplitWin.SetSashPosition(w*(2.0/3))
        mainSplitWin = self.getWidget("MainSplitterWindow")
        mainSplitWin.SetSashPosition(h*(2.0/3))
        
        # init the entity choice widget
        entChoiceHost = self.getWidget("EntityChoicePanel")
        sizer = entChoiceHost.GetSizer()#wx.Sizer(box, wx.HORIZONTAL)
        self._entityChoice = EntitySelectionChoice(entChoiceHost, self._controller)
        sizer.Add(self._entityChoice, 1, wx.ALL|wx.EXPAND)
        entChoiceHost.SetSizer(sizer)
        
        # Install the scenegraph
        sgHost = self.getWidget("SceneGraphPage")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sgHost.SetSizer(sizer)
        self._sgTree = SceneGraphTree(sgHost, self._controller)
        sizer.Add(self._sgTree, 1, wx.EXPAND | wx.TR_LINES_AT_ROOT | 
                  wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE | wx.SIMPLE_BORDER)
        
        # Install the the property grid
        propGridHost = self.getWidget("PropertiesPage")
        sizer = wx.BoxSizer(wx.VERTICAL)
        propGridHost.SetSizer(sizer)
        self.propertyGrid = PropertyGrid(propGridHost, style=wx.EXPAND|wx.ALL )
        sizer.Add(self.propertyGrid, 1, wx.EXPAND)

    def _bindEvents(self):
        # window resize and quit
        self.frame.Bind(wx.EVT_SIZE, self.onSize)
        self.frame.Bind(wx.EVT_CLOSE, self.onQuit)
        
        # menubar
        # wxEVT_COMMAND_MENU_SELECTED
        menuBar = self.frame.GetMenuBar()
        
        # Binding toolbar items 
        # I wish there was a better way...
        toolbar = self.frame.GetToolBar()
        tools = ("NewButton","OpenButton","SaveButton","CopyButton",
                 "PasteButton","DeleteButton","UndoButton","RedoButton")
        
        for tool in tools:
            toolId = xrc.XRCID(tool)
            callback = eval("self._controller.on%sClicked" % tool)
            self.frame.Bind(wx.EVT_TOOL,callback,id=toolId)
        
        # various bindings
        self.frame.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.onSize)
        self.frame.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.onSize)
     
    def MainLoop(self, task = None):
        while self.evtLoop.Pending(): 
            self.evtLoop.Dispatch()
        self.ProcessIdle()
        
        if task != None: return task.cont
        
        return True
