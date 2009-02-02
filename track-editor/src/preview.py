# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG,WARNING
logger = ConsoleLogger("preview", DEBUG)

from pandac.PandaModules import loadPrcFileData
loadPrcFileData("", "show-frame-rate-meter t")
loadPrcFileData("", "window-type none")

from direct.showbase.DirectObject import DirectObject

import direct.directbase.DirectStart
from direct.gui.OnscreenText import OnscreenText

from pandac.PandaModules import WindowProperties, Point3, Vec3, NodePath, \
Filename, CollisionTraverser,CollisionHandlerQueue, CollisionNode, GeomNode, \
CollisionRay

from mdlib.panda.sheet import Sheet
from mdlib.panda.math_utils import pointAtZ

from gui.qt.plugins.tileeditorview import Tile 


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


VERTEX_PER_ROW = 4

class TrackGenerator(DirectObject):   
    def __init__(self):
        self.isWireframe = False
        self.objectName = None
        
        self.accept("mouse1", self.grabPoint)
        self.accept("mouse1-up", self.releasePoint)
        self.accept("p", self.save)
        self.accept("b", self.toggleOobe)
        self.accept("r", self.toggleRenderMode)
        self.accept("escape", self.hideTrack)
        
        self.selectedObject = None
        self.points = []
        self.surface = None
        
    def toggleRenderMode(self):
        if self.isWireframe:
            base.wireframeOff()
            self.isWireframe = False
        else:
            base.wireframeOn()
    
    def toggleOobe(self):
        base.oobe()
    
    def grabPoint(self):
        logger.debug("Dragging point")
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
        logger.debug("Releasing point")
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
        filename = "/tmp/test.egg"
        logger.debug("Saving surface to " % filename)
        egg = self.surface.toEgg()
        egg.writeEgg(Filename(filename))
    
    def generate(self, tiles, x=0,y=0,z=0):
        verts = []
        vertexDistance = 2
        """
        for row in tiles:
            realTiles = filter(lambda x: x is not None, row)
            if len(realTiles) > 0:
                firstTile = realTiles[0]
                lastTile = realTiles[-1]
                
                yIncrement = (lastTile.y -firstTile.y) / float(VERTEX_PER_ROW)
                if len(realTiles) == 1:
                    yIncrement = 1.0/ float(VERTEX_PER_ROW)
                for i in range(VERTEX_PER_ROW):
                    y = firstTile.y + (i * yIncrement) + yIncrement/2.0
                    x, z = firstTile.x, firstTile.z
                    # FIXME
                    color = self._colorForTile(realTiles[0].color)
                    vert = {'node':None, 'point': (x,y,z), 
                                    'color' : color}
                    verts.insert(0,vert)

        """
        verts = []
        color = (1,1,1,0)
        for i in range(10):
            vert = {'node':None, 'point': (i,0.875,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.625,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.375,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.175,z), 'color' : color}
            verts.append(vert)
    
        for row in tiles:
            realTiles = filter(lambda x: x is not None, row)
            if len(realTiles) > 0:
                firstTile = realTiles[0]
                lastTile = realTiles[-1]
                
                xIncrement = (lastTile.x - firstTile.x+1) / float(VERTEX_PER_ROW)
                if len(realTiles) == 1:
                    xIncrement = 1.0/ float(VERTEX_PER_ROW)
                for i in range(VERTEX_PER_ROW):
                    x = firstTile.x + (i * xIncrement) + xIncrement/2.0
                    y, z = firstTile.y, firstTile.z
                    # FIXME
                    color = self._colorForTile(realTiles[0].color)
                    vert = {'node':None, 'point': (x,y,z), 
                                    'color' : color}
                    verts.append(vert)
                print realTiles
                
        self.generateSurface(verts)
                    
    def generateSurface(self, verts):
        surface = Sheet("curve")
        surface.setup(4,4,VERTEX_PER_ROW, verts)
        surface.sheetNode.setNumUSubdiv(VERTEX_PER_ROW)
        #surface.sheetNode.setNumVSubdiv(4)
        #surface.setTwoSided(True)
        
        # draw control points
        points = [v['point'] for v in verts]
        points = map(lambda x: map(lambda y: float(y), x), points)
        for idx, point in enumerate(points):
            p = loader.loadModel( '../res/models/point.egg' )
            p.setScale(0.1)
            if idx == 0:
                p.setColor(0,0,1,0)
            else:
                p.setColor(1,0,0,0)
            p.setPos(Point3(point[0],point[1],point[2]))
            p.setTag("idx", "%s" % idx)
            p.reparentTo(surface)
            self.points.append(p)
        
        if self.surface is not None:
            self.surface.removeNode()
        self.surface = surface
        
    def update(self):
        taskMgr.step()
    
    def hideTrack(self):
        base.closeWindow(base.winList[0])
        self.isVisible = False
    
    def showTrack(self, windowHandle=None):
        wp = WindowProperties().getDefault()
        wp.setOrigin(0,0)
        wp.setSize(800, 600)
        if windowHandle is not None:
            wp.setParentWindow(windowHandle)
        base.openDefaultWindow(props=wp)

        self.cam = Camera()
        base.oobe()
        self._setupCollisionDetection()
        self.surface.reparentTo(render)
        self.mouseTask = taskMgr.add(self.mouseTask, "mouseTask")
        self.isVisible = True
        
        self._startPanda()
        
    def _startPanda(self):
        import time
        while self.isVisible:
            taskMgr.step()
            time.sleep(0.001)
            
    def _colorForTile(self, tileColor):
        color = (0,0,0,0)
        if tileColor <= 3:
            color = (1,1,1,0)
        elif tileColor == 7:
            color = (1,0,1,0)
        elif tileColor == 8:
            color = (0,1,0,0)
        elif tileColor == 9:
            color = (0,0,1,0)
        elif tileColor == 12:
            color = (1,1,0,0)
        
        return color   
        
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
  
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
