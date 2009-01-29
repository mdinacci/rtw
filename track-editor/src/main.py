# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""
from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "show-frame-rate-meter t")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText

from pandac.PandaModules import WindowProperties, Point3, Vec3, NodePath, \
Filename, CollisionTraverser,CollisionHandlerQueue, CollisionNode, GeomNode, \
CollisionRay

from mdlib.panda.sheet import Sheet
from mdlib.panda.math_utils import pointAtZ

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.autogen import *

import sys

class Camera(object):
    FORWARD = Vec3(0,2,0)
    BACK = Vec3(0,-1,0)
    LEFT = Vec3(-1,0,0)
    RIGHT = Vec3(1,0,0)
    UP = Vec3(0,0,1)
    DOWN = Vec3(0,0,-1)
    STOP = Vec3(0)
    walk = STOP
    strafe = STOP
    ZOOM_SPEED = 5
    
    def __init__(self):
        self.createVirtualNode()
        self.setupCamera()
        self.attachControls()
        
        self.linearSpeed = 100
        #taskMgr.add(self.mouseUpdate, 'mouse-task')
        taskMgr.add(self.moveUpdate, 'move-task')
        
    def attachControls(self):
        base.accept( "s" , self.__setattr__,["walk",self.STOP] )
        base.accept( "w" , self.__setattr__,["walk",self.FORWARD])
        base.accept( "s" , self.__setattr__,["walk",self.BACK] )
        base.accept( "s-up" , self.__setattr__,["walk",self.STOP] )
        base.accept( "w-up" , self.__setattr__,["walk",self.STOP] )
        base.accept( "a" , self.__setattr__,["strafe",self.LEFT])
        base.accept( "d" , self.__setattr__,["strafe",self.RIGHT] )
        base.accept( "a-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "d-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "q" , self.__setattr__,["strafe",self.UP] )
        base.accept( "q-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept( "e" , self.__setattr__,["strafe",self.DOWN] )
        base.accept( "e-up" , self.__setattr__,["strafe",self.STOP] )
        base.accept('wheel_up-up', self.zoomIn)
        base.accept('wheel_down-up', self.zoomOut)
    
    def zoomOut(self):
        base.camera.setY(base.camera, - self.ZOOM_SPEED)

    def zoomIn(self):
        base.camera.setY(base.camera,  self.ZOOM_SPEED)
        
    def createVirtualNode(self):
        self.node = NodePath("vcam")
        self.node.reparentTo(render)
        self.node.setPos(0,0,2)
        self.node.setScale(0.05)
        self.node.showBounds()

    def setupCamera(self):
        base.disableMouse()
        camera.setPos( 6, -100, 150)
        camera.lookAt(0,0,0)
        camera.reparentTo(self.node)
    
    def mouseUpdate(self,task):
        """ this task updates the mouse """
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
            self.node.setH(self.node.getH() -  (x - base.win.getXSize()/2)*0.3)
            base.camera.setP(base.camera.getP() - (y - base.win.getYSize()/2)*0.3)
        return task.cont

    def moveUpdate(self,task):
        """ this task makes the vcam move """
        # move where the keys set it
        self.node.setPos(self.node,self.walk*globalClock.getDt()*self.linearSpeed)
        self.node.setPos(self.node,self.strafe*globalClock.getDt()*self.linearSpeed)
        return task.cont


class GUI(QMainWindow):
    def __init__(self, view, *args):
        apply(QMainWindow.__init__, (self,) + args)
        
        self.view = view

        self._setupUi()
        
        timer =  QTimer(self)
        self.connect(timer, SIGNAL("timeout()"), self.view.update)
        timer.start(0)
    
    def __getattr__(self,attr):
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self._mainWin.__dict__[attr]
         
    def _setupUi(self):
        self.setWindowTitle("Test")
        self.setGeometry(0,0,800,600)
        
        self._mainWin = Ui_MainWindow()
        self._mainWin.setupUi(self)
        
        self.centralwidget.resizeEvent = self.resizeP3DWindow
        
    def resizeP3DWindow(self, event):
        """ 
        Called when a resize event is sent by QT. 
        Used to resize the p3d window
        """
        size = event.size()
        # at app startup pandaWindow is not set yet
        if base.win != None:
            pandaWin = self
            pandaWin = self._mainWin.p3dContainer
            w,h = size.width(), size.height()
            wp = WindowProperties()
            
            # FIXME detect widget position wrt parent
            wp.setOrigin(1, 1)
            
            minW = pandaWin.minimumWidth()
            minH = pandaWin.minimumHeight()
            
            if w < minW:
                w = minW
            if h < minH:
                h = minH
            
            wp.setSize(w, h)
            base.win.requestProperties(wp)
        
            # FIXME doesnt' work
            messenger.send('window-event',[base.win])
        
        self.update()
           

class World(DirectObject):   
    def __init__(self):
        self.cam= Camera()
        base.oobe()
        self.isWireframe = False
        self.objectName = None
        
        self.mouseTask = taskMgr.add(self.mouseTask, "mouseTask")
        self.accept("mouse1", self.grabPoint)
        self.accept("mouse1-up", self.releasePoint)
        self.accept("p", self.save)
        self.accept("b", self.toggleOobe)
        self.accept("r", self.toggleRenderMode)
        
        self.selectedObject = None
        self.points = []
        self._setupCollisionDetection()
        
        self.surface = self.createSheet("sheet1")
    
    def toggleRenderMode(self):
        if self.isWireframe:
            base.wireframeOff()
            self.isWireframe = False
        else:
            base.wireframeOn()
    
    def toggleOobe(self):
        base.oobe()
    
    def grabPoint(self):
        if base.mouseWatcherNode.hasMouse():
            mousePos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mousePos.getX(), mousePos.getY())
            self.picker.traverse(self.surface)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                    
                pickedObject = self.pq.getEntry(0).getIntoNodePath()
                self.selectedObject = pickedObject
                
                name = self.selectedObject.getName()
                if self.objectName is not None:
                    self.objectName.destroy()
                
                self.objectName = OnscreenText(text=name,style=1, fg=(1,1,1,1),
                                      pos=(0.8,-0.95), scale = .07)

    def releasePoint(self):
        self.surface.recompute()
        self.selectedObject = None
        
    def mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            
            if self.selectedObject is not None:
                nearPoint = render.getRelativePoint(camera, self.pickerRay.getOrigin())
                nearVec = render.getRelativeVector(camera, self.pickerRay.getDirection())
                pos = pointAtZ(0, nearPoint, nearVec)
                self.selectedObject.setPos(pos)
                
                v = self.surface.verts[int(self.selectedObject.getNetTag("idx"))]
                v["point"] = pos
                
                self.surface.recompute()
        
        return task.cont
        
    def save(self):
        egg = self.surface.toEgg()
        egg.writeEgg(Filename("/tmp/test.egg"))
    
    def createSheet(self, name, x=0,y=0,z=0):
        """
        verts = [
         {'node':None, 'point': (-7.5, -8., 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7.5, -8, 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-9.8, -2.7, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-5.3, -7.2, -3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (5.3, -7.2, -3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (9.8, -2.7, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-11., 4.0, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-6., -1.8, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (6., -1.8, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (11, 4.0, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         ]
        """
        verts = [
                 {'node':None, 'point': (3, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (6, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (9, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (12, 0, 0), 'color' : (0,0,0,0)} ,
                 
                 {'node':None, 'point': (3, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (6, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (9, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (12, 3, 0), 'color' : (0,1,0,0)} ,
                 
                 {'node':None, 'point': (3, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (6, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (9, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (12, 6, 0), 'color' : (0,0,1,0)} ,
                 
                 {'node':None, 'point': (3, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 10, 0), 'color' : (0,1,1,0)}
                 ,
        
                 {'node':None, 'point': (3, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 12, 0), 'color' : (0,1,1,0)},
                 
                 {'node':None, 'point': (3, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 14, 0), 'color' : (0,1,1,0)}
         ]
        surface2 = Sheet("curve")
        surface2.setup(4,4,4, verts)
        surface2.sheetNode.setNumUSubdiv(4)
        surface2.sheetNode.setNumVSubdiv(10)
        surface2.reparentTo(render)
        #surface2.flattenStrong()
        surface2.setTwoSided(True)
        
        points = [v['point'] for v in verts]
        for idx, point in enumerate(points):
            p = loader.loadModel( '../res/models/point.egg' )
            p.setScale(0.1)
            if idx == 0:
                p.setColor(0,0,1,0)
            else:
                p.setColor(1,0,0,0)
            p.setPos(Point3(point[0],point[1],point[2]))
            p.setTag("idx", "%s" % idx)
            p.reparentTo(surface2)
            self.points.append(p)
        
        return surface2
    
    def update(self):
        taskMgr.step()
    
    def bindToWindow(self, windowHandle):
        wp = WindowProperties().getDefault()
        wp.setOrigin(0,0)
        wp.setSize(400, 300)
        wp.setParentWindow(windowHandle)
        base.openDefaultWindow(props=wp)
        
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        #self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
  
    
if __name__ == '__main__':
    world = World()

    app = QApplication(sys.argv)
    form = GUI(world)
    world.bindToWindow(form.winId())
    
    form.show()
    app.exec_()
    
