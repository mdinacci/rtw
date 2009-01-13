# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText

class EditViewGUI(object):
    """
    This GUI is used while editing the world in EditMode.
    It contains widgets that allow adding and modifying properties
    of the world. 
    
    TODO create the gui separately and use it here
    """
    def __init__(self, controller):
        self.controller = controller
        maps = loader.loadModel('delete_btn/delete_btn.egg')
        ra = base.camLens.getAspectRatio()
        
        self.leftMenu = DirectFrame(parent=aspect2d,
                                    frameColor=(0,0,1,.3), 
                                    frameSize=(-1.5,0.7,-1.5,0.7),
                                    pos = (-.8*ra,0,.6*ra))
        
        self._widgets = [self.leftMenu]
        
        deleteBtn = DirectButton(geom = (maps.find('**/delete'),
                         maps.find('**/delete'),
                         maps.find('**/delete_over'),
                         maps.find('**/delete')),
                         borderWidth=(0,0),
                         frameColor=(0,0,0,0),
                         scale = .1,
                         pos = (-.1,0,-.4),
                         command=self.controller.onDeleteButtonClick)
        deleteBtn.hide()
        self._widgets.append(deleteBtn)
        
        worldMenu = DirectOptionMenu(text="World Type", scale=0.1,
                                        items=["Mountain","Space","Forest"],
                                        initialitem=0, 
                                        borderWidth=(0,0),
                                        highlightColor=(0.65,0.65,0.65,1),
                                        pos = (-.2,0,0),
                                        command=self.controller.onWorldButtonClick)
        worldMenu.hide()
        self._widgets.append(worldMenu)

        cellTypeMenu = DirectOptionMenu(text="Cell Type", scale=0.1,
                                        items=["Normal","Speed","Jump","Teleport",
                                               "Invert","Bounce Back"],
                                        initialitem=0, 
                                        borderWidth=(0,0),
                                        highlightColor=(0.65,0.65,0.65,1),
                                        pos = (-.2,0,-.2),
                                        command=self.controller.onCellNatureClick)
        cellTypeMenu.hide()
        self._widgets.append(cellTypeMenu)
        
        for widget in self._widgets[1:]:
            widget.reparentTo(self.leftMenu)
        
    @eventCallback
    def editNode(self, nodepath):
        # show properties editor
        pass
        
    def enable(self):
        for widget in self._widgets:
            widget.show()
    
    def disable(self):
        for widget in self._widgets:
            widget.hide()

