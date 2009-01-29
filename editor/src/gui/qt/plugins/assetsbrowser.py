# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

class ImagePopup(QLabel):
    """ 
    The ImagePopup class is a QLabel that displays a popup, zoomed image 
    on top of another label.  
    """
    def __init__(self, parent):
        super(QLabel, self).__init__(parent)
        
        thumb = parent.pixmap()
        imageSize = thumb.size()
        imageSize.setWidth(imageSize.width()*2)
        imageSize.setHeight(imageSize.height()*2)
        self.setPixmap(thumb.scaled(imageSize,Qt.KeepAspectRatioByExpanding))
        
        # center the zoomed image on the thumb
        position = self.cursor().pos()
        position.setX(position.x() - thumb.size().width())
        position.setY(position.y() - thumb.size().height())
        self.move(position)
        
        # FramelessWindowHint may not work on some window managers on Linux
        # so I force also the flag X11BypassWindowManagerHint
        self.setWindowFlags(Qt.Popup | Qt.WindowStaysOnTopHint 
                            | Qt.FramelessWindowHint 
                            | Qt.X11BypassWindowManagerHint)

    def leaveEvent(self, event):
        """ When the mouse leave this widget, destroy it. """
        self.destroy()
        

class ImageLabel(QLabel):
    """ This widget displays an ImagePopup when the mouse enter its region """
    def enterEvent(self, event):
        self.p = ImagePopup(self)
        self.p.show()
        event.accept() 

class AssetsBrowser(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.setWindowTitle("Asset Browser")
        self.setLayout(QGridLayout(self))
    
    def populate(self, pics, size, imagesPerRow=4, 
                 flags=Qt.KeepAspectRatioByExpanding):
        row = col = 0
        for pic in pics:
            label = ImageLabel("")
            pixmap = QPixmap(pic)
            pixmap = pixmap.scaled(size, flags)
            label.setPixmap(pixmap)
            self.layout().addWidget(label, row, col)
            col +=1
            if col % imagesPerRow == 0:
                row += 1
                col = 0
