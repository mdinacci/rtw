# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ropegui.ui'
#
# Created: Mon Jan 26 15:56:18 2009
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.p3dContainer = QtGui.QWidget(self.centralwidget)
        self.p3dContainer.setGeometry(QtCore.QRect(0, 0, 391, 251))
        self.p3dContainer.setObjectName("p3dContainer")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))


class Ui_DockWidget(object):
    def setupUi(self, DockWidget):
        DockWidget.setObjectName("DockWidget")
        DockWidget.resize(300, 284)
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.widget = QtGui.QWidget(self.dockWidgetContents)
        self.widget.setGeometry(QtCore.QRect(10, 14, 271, 241))
        self.widget.setObjectName("widget")
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.point_1 = QtGui.QLineEdit(self.widget)
        self.point_1.setObjectName("point_1")
        self.verticalLayout.addWidget(self.point_1)
        self.point_2 = QtGui.QLineEdit(self.widget)
        self.point_2.setObjectName("point_2")
        self.verticalLayout.addWidget(self.point_2)
        self.point_3 = QtGui.QLineEdit(self.widget)
        self.point_3.setObjectName("point_3")
        self.verticalLayout.addWidget(self.point_3)
        self.point_4 = QtGui.QLineEdit(self.widget)
        self.point_4.setObjectName("point_4")
        self.verticalLayout.addWidget(self.point_4)
        self.point_5 = QtGui.QLineEdit(self.widget)
        self.point_5.setObjectName("point_5")
        self.verticalLayout.addWidget(self.point_5)
        self.point_6 = QtGui.QLineEdit(self.widget)
        self.point_6.setObjectName("point_6")
        self.verticalLayout.addWidget(self.point_6)
        self.pushButton = QtGui.QPushButton(self.widget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)
        QtCore.QMetaObject.connectSlotsByName(DockWidget)

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle(QtGui.QApplication.translate("DockWidget", "DockWidget", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("DockWidget", "Extrude", None, QtGui.QApplication.UnicodeUTF8))

