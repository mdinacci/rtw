# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui.ui'
#
# Created: Mon Feb  9 14:26:03 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setDockNestingEnabled(True)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.p3dContainer = QtGui.QWidget(self.centralwidget)
        self.p3dContainer.setGeometry(QtCore.QRect(0, 0, 791, 521))
        self.p3dContainer.setObjectName("p3dContainer")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtGui.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.newButton = QtGui.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/document-new.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.newButton.setIcon(icon)
        self.newButton.setObjectName("newButton")
        self.openButton = QtGui.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/document-open.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.openButton.setIcon(icon1)
        self.openButton.setObjectName("openButton")
        self.saveButton = QtGui.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/document-save.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.saveButton.setIcon(icon2)
        self.saveButton.setObjectName("saveButton")
        self.actionSave_As = QtGui.QAction(MainWindow)
        self.actionSave_As.setIcon(icon2)
        self.actionSave_As.setObjectName("actionSave_As")
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName("actionQuit")
        self.copyButton = QtGui.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/edit-copy.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.copyButton.setIcon(icon3)
        self.copyButton.setObjectName("copyButton")
        self.pasteButton = QtGui.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/edit-paste.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pasteButton.setIcon(icon4)
        self.pasteButton.setObjectName("pasteButton")
        self.deleteButton = QtGui.QAction(MainWindow)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/list-remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon5.addPixmap(QtGui.QPixmap(":/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.deleteButton.setIcon(icon5)
        self.deleteButton.setObjectName("deleteButton")
        self.undoButton = QtGui.QAction(MainWindow)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/edit-undo.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.undoButton.setIcon(icon6)
        self.undoButton.setObjectName("undoButton")
        self.redoButton = QtGui.QAction(MainWindow)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/edit-redo.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.redoButton.setIcon(icon7)
        self.redoButton.setObjectName("redoButton")
        self.addButton = QtGui.QAction(MainWindow)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/list-add.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.addButton.setIcon(icon8)
        self.addButton.setObjectName("addButton")
        self.menuFile.addAction(self.newButton)
        self.menuFile.addAction(self.openButton)
        self.menuFile.addAction(self.saveButton)
        self.menuFile.addAction(self.actionSave_As)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuEdit.addAction(self.copyButton)
        self.menuEdit.addAction(self.pasteButton)
        self.menuEdit.addAction(self.deleteButton)
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.undoButton)
        self.menuEdit.addAction(self.redoButton)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.toolBar.addAction(self.newButton)
        self.toolBar.addAction(self.openButton)
        self.toolBar.addAction(self.saveButton)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.copyButton)
        self.toolBar.addAction(self.pasteButton)
        self.toolBar.addAction(self.addButton)
        self.toolBar.addAction(self.deleteButton)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.undoButton)
        self.toolBar.addAction(self.redoButton)
        self.toolBar.addSeparator()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "Editor v0.1", None, QtGui.QApplication.UnicodeUTF8))
        self.menuFile.setTitle(QtGui.QApplication.translate("MainWindow", "File", None, QtGui.QApplication.UnicodeUTF8))
        self.menuEdit.setTitle(QtGui.QApplication.translate("MainWindow", "Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.newButton.setText(QtGui.QApplication.translate("MainWindow", "New", None, QtGui.QApplication.UnicodeUTF8))
        self.newButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+N", None, QtGui.QApplication.UnicodeUTF8))
        self.openButton.setText(QtGui.QApplication.translate("MainWindow", "Open", None, QtGui.QApplication.UnicodeUTF8))
        self.openButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+O", None, QtGui.QApplication.UnicodeUTF8))
        self.saveButton.setText(QtGui.QApplication.translate("MainWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.saveButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+S", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_As.setText(QtGui.QApplication.translate("MainWindow", "Save As", None, QtGui.QApplication.UnicodeUTF8))
        self.actionSave_As.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Shift+S", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.copyButton.setText(QtGui.QApplication.translate("MainWindow", "Copy", None, QtGui.QApplication.UnicodeUTF8))
        self.copyButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+C", None, QtGui.QApplication.UnicodeUTF8))
        self.pasteButton.setText(QtGui.QApplication.translate("MainWindow", "Paste", None, QtGui.QApplication.UnicodeUTF8))
        self.pasteButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+V", None, QtGui.QApplication.UnicodeUTF8))
        self.deleteButton.setText(QtGui.QApplication.translate("MainWindow", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.deleteButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+D", None, QtGui.QApplication.UnicodeUTF8))
        self.undoButton.setText(QtGui.QApplication.translate("MainWindow", "Undo", None, QtGui.QApplication.UnicodeUTF8))
        self.redoButton.setText(QtGui.QApplication.translate("MainWindow", "Redo", None, QtGui.QApplication.UnicodeUTF8))
        self.addButton.setText(QtGui.QApplication.translate("MainWindow", "Add Entity", None, QtGui.QApplication.UnicodeUTF8))
        self.addButton.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+A", None, QtGui.QApplication.UnicodeUTF8))

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scenegraph.ui'
#
# Created: Mon Feb  9 14:26:04 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_toolsDock(object):
    def setupUi(self, toolsDock):
        toolsDock.setObjectName("toolsDock")
        toolsDock.setWindowModality(QtCore.Qt.NonModal)
        toolsDock.resize(350, 427)
        toolsDock.setFloating(False)
        toolsDock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.horizontalLayout = QtGui.QHBoxLayout(self.dockWidgetContents)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.toolBox = QtGui.QToolBox(self.dockWidgetContents)
        self.toolBox.setObjectName("toolBox")
        self.sgPage = QtGui.QWidget()
        self.sgPage.setGeometry(QtCore.QRect(0, 0, 332, 327))
        self.sgPage.setObjectName("sgPage")
        self.horizontalLayoutWidget = QtGui.QWidget(self.sgPage)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 331, 321))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.sceneGraphView = SceneGraphView(self.horizontalLayoutWidget)
        self.sceneGraphView.setObjectName("sceneGraphView")
        self.horizontalLayout_2.addWidget(self.sceneGraphView)
        self.toolBox.addItem(self.sgPage, "")
        self.page_2 = QtGui.QWidget()
        self.page_2.setGeometry(QtCore.QRect(0, 0, 332, 327))
        self.page_2.setObjectName("page_2")
        self.gridLayoutWidget = QtGui.QWidget(self.page_2)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 331, 321))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.toolBox.addItem(self.page_2, "")
        self.horizontalLayout.addWidget(self.toolBox)
        toolsDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(toolsDock)
        self.toolBox.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(toolsDock)

    def retranslateUi(self, toolsDock):
        toolsDock.setWindowTitle(QtGui.QApplication.translate("toolsDock", "Tools", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBox.setItemText(self.toolBox.indexOf(self.sgPage), QtGui.QApplication.translate("toolsDock", "Page 1", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QtGui.QApplication.translate("toolsDock", "Page 2", None, QtGui.QApplication.UnicodeUTF8))

from gui.qt.plugins.scenegraphview import SceneGraphView
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'entityinspector.ui'
#
# Created: Mon Feb  9 14:26:04 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_EntityInspectorDock(object):
    def setupUi(self, EntityInspectorDock):
        EntityInspectorDock.setObjectName("EntityInspectorDock")
        EntityInspectorDock.resize(350, 380)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.horizontalLayout = QtGui.QHBoxLayout(self.dockWidgetContents)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.entityInspector = EntityInspector(self.dockWidgetContents)
        self.entityInspector.setObjectName("entityInspector")
        self.horizontalLayout.addWidget(self.entityInspector)
        EntityInspectorDock.setWidget(self.dockWidgetContents)

        self.retranslateUi(EntityInspectorDock)
        QtCore.QMetaObject.connectSlotsByName(EntityInspectorDock)

    def retranslateUi(self, EntityInspectorDock):
        EntityInspectorDock.setWindowTitle(QtGui.QApplication.translate("EntityInspectorDock", "DockWidget", None, QtGui.QApplication.UnicodeUTF8))

from gui.qt.plugins.entityinspector import EntityInspector
