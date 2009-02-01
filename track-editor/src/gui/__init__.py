from autogen import *

from PyQt4.QtGui import *
from PyQt4.QtCore import *

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    form = Ui_MainWindow()
    w = QMainWindow()
    form.setupUi(w)
    
    dock = Ui_AssetsDockWidget()
    dockWidget = QDockWidget(w)
    dock.setupUi(dockWidget)
    w.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
    
    from gui.qt.plugins.assetsbrowser import AssetsController as ac
    
    c = ac(dock.assetsBrowser)
    app.connect(dock.addButton, SIGNAL("clicked()"), c.addRepository)
    app.connect(dock.removeButton, SIGNAL("clicked()"), c.removeRepository)
    
    w.show()
    app.exec_()