# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("widgets", DEBUG)

from wx.grid import *
import wx

class EntitySelectionChoice(wx.Choice):
    def __init__(self, parent, controller):
        wx.Choice.__init__(self, parent, style=wx.EXPAND)
        self._controller = controller
        
    def populate(self):
        self.Clear()
        entities = map(lambda x: str(x), self._controller.getEntities())
        self.AppendItems(entities)
        self.Select(0)
        

class SceneGraphTree(wx.TreeCtrl):
    """A treeview object to show the Scene Graph."""

    def __init__(self, parent, controller):
        wx.TreeCtrl.__init__(self, parent, style=wx.TR_HAS_BUTTONS |
                             wx.TR_DEFAULT_STYLE | wx.SUNKEN_BORDER | wx.EXPAND)
        
        self._controller = controller

        # construct image list
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        gb = wx.ArtProvider_GetBitmap
        self._images = {"branch": il.Add(gb(wx.ART_FOLDER, wx.ART_OTHER, isz)), 
                        "branchOpen":il.Add(gb(wx.ART_FILE_OPEN, wx.ART_OTHER, isz)), 
                        "leaf": il.Add(gb(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))}
        self.SetImageList(il)
        self.il = il
        
        # register controller to events
        self.Bind(wx.EVT_TREE_SEL_CHANGED, 
                  self._controller.onSceneGraphSelectionChange)
        
        self.populate()
        
    def populate(self):
        def _populateTree(pandaRoot, treeNode):
            children = pandaRoot.getChildren().asList()
            for child in children:
                print "Processing node: ", child
                # if child has children recursively add them to the tree
                if child.getNumChildren() > 0:
                    print "%d children" % child.getNumChildren()
                    item = self.AppendItem(treeNode, child.getName())
                    print "item appended"
                    self.SetItemImage(item, self._images["branch"], wx.TreeItemIcon_Normal)
                    self.SetItemImage(item, self._images["branchOpen"], wx.TreeItemIcon_Expanded)
                    self.SetPyData(item, None)
                    print "calling again populatetree"
                    _populateTree(child, item)
                else:
                    print "no children"
                    item = self.AppendItem(treeNode, child.getName())
                    self.SetItemImage(item, self._images["leaf"], wx.TreeItemIcon_Normal)
                    self.SetPyData(item, None)
            
            
        pandaRoot = self._controller.getSceneGraphRoot()
        
        if pandaRoot is not None:
            self.DeleteAllItems()
            self.root = self.AddRoot("Scenegraph tree")
            self.SetItemImage(self.root, self._images["branch"], wx.TreeItemIcon_Normal)
            self.SetItemImage(self.root, self._images["branchOpen"], wx.TreeItemIcon_Expanded)
            logger.debug("Populating scene graph browser")
            _populateTree(pandaRoot, self.root)
            self.Expand(self.root)
        

    """
    def selectNodePath(self, model):
        ""Selects the given NodePath in the tree.""
        if model in self.modelDict:
          treeItem = self.modelDict[model]
          self.ignoreSelChange = True
          self.SelectItem(treeItem)
          self.ignoreSelChange = False
      
    def reload(self):
        ""Clears the tree view and reloads it based on the scene graph.""
        self.DeleteAllItems()
        self.modelDict.clear()
        
        # Create the root render node
        renderId = self.AddRoot("render")
        # render should send a pydata None (deselects all models)
        self.SetItemPyData(renderId, None)
        self.__appendChildren(renderId, base.render)
        self.modelDict[None] = renderId
        self.Expand(renderId)
        # Force a select event.
        self.onSelChange(renderId)
      
    def __appendChildren(self, treeParent, nodePath):
        ""Used internally to recursively add the children of a nodepath to 
        the scene graph browser.""
        for c in xrange(nodePath.getNumChildren()):
          childNodePath = nodePath.getChild(c)
          childModel = modelIdManager.getObject(modelIdManager.getObjectId(childNodePath))
          if childNodePath.hasTag(ENABLE_SCENEGRAPHBROWSER_MODEL_TAG):
            treeItem = self.AppendItem(treeParent, childNodePath.getName())
            self.SetItemPyData(treeItem, childModel)
            self.modelDict[childNodePath] = treeItem
            # Iterate through the children
            self.__appendChildren(treeItem, childNodePath)
    """

def makeRenderer(type):
    """Returns a new GridCellRenderer for the given property type."""
    if type == bool: # Bool must be checked before int
        return GridCellBoolRenderer()
    elif type == int or type == long:
        return GridCellNumberRenderer()
    elif type == float:
        return GridCellFloatRenderer()
    else:
        return GridCellStringRenderer()

def makeEditor(type):
    """Returns a new GridCellEditor for the given property type."""
    if type == bool: # Bool must be checked before int
        return GridCellBoolEditor()
    elif type == int or type == long:
        return GridCellNumberEditor()
    elif type == float:
        return GridCellFloatEditor()
    elif isinstance(type, dict):
        return GridCellChoiceEditor(type.keys())
    else:
        return GridCellTextEditor() 


class PropertyGrid(Grid):
    """The grid to edit node properties."""
    def __init__(self, *args, **kwargs):
        Grid.__init__(self, *args, **kwargs)
        #self.EnableScrolling(False, False)
        self.EnableEditing(True)
        self.CreateGrid(10, 2)
        # Catch events
        self.Bind(wx.EVT_SIZE, self.onSize)
        #self.Bind(EVT_GRID_CELL_CHANGE, self.onCellChange)
        self._configure()
    
    def _configure(self):
        self.SetRowLabelSize(0)
        self.SetColLabelSize(0)
        #self.SetSelectionMode(0)
        
        self.onSize()
  
    def onSize(self, evt = None):
        """ Invoked when the size has changed."""
        w,h = self.GetClientSizeTuple()
        self.SetColSize(0, w * (1.9/3) )
        self.SetColSize(1, w * (1.0/3) )
      
    def reset(self, row=0, col=0):
        """Entirely resets the grid."""
        self.ClearGrid()
        if self.GetNumberRows() > 0:
          self.DeleteRows(0, self.GetNumberRows())
        if row > 0 or col > 0:
            self.CreateGrid(row,col)
            self._configure()
      
    def addProperty(self, propName, propType, value = None):
        """ Adds a new property to the control. """

        self.AppendRows(1, False)
        row = self.GetNumberRows() - 1
        self.SetCellValue(row, 0, propName)
        #self.SetReadOnly(row, 0, True)
        #self.SetReadOnly(row, 1, False)
        #self.SetCellRenderer(row, 1, makeRenderer(propType))
        #self.SetCellEditor(row, 1, makeEditor(propType))
        self.SetCellValue(row, 1, str(value))
      
    def onCellChange(self, evt):
         """Invoked when a cell is modified."""
         if self.object == None: return
         if evt.Col != 1: return
         name = self.GetCellValue(evt.Row, 0)
         value = self.GetCellValue(evt.Row, 1)
         try:
           self.object.setParameter(name, value)
           #FIXME: If it changed the nodepath name, it should reload the scene graph tree.
           #if prop.setter == NodePath.setName:
           #  messenger.send(EVENT_SCENEGRAPHBROWSER_REFRESH)
         except Exception, ex: # Stop the change if the value is invalid.
           evt.Veto()
           print "Exception in oncellchange"
           raise
         self.SetCellValue(evt.Row, 1, str(self.object.getParameter(name)))

    #def viewForNodePath(self, nodePath):
    #    """Updates the control based on the specified NodePath."""
    #    self.reset()
    #    self.object = nodePath
    #    if nodePath == None: return
    #    for propName, prop in nodePath.mutableParameters.items():
    #      if prop != None:
    #        self.addProperty(propName, prop[0], nodePath.getParameter(propName))
    #  
    #def viewForSelection(self):
    #    """Similar to viewForNodePath, but this uses the currently selected model."""
    #    return self.viewForNodePath(modelController.getSelectedModel())
