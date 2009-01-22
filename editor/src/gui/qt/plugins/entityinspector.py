# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from PyQt4.QtGui import QTreeView

class EntityInspector(QTreeView):
    
    def __init__(self, parent=None):
        super(EntityInspector, self).__init__(parent)

