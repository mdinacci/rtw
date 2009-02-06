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
from mdlib.math import transpose2DMatrix, rotateMatrixClockwise, \
rotateMatrixAntiClockwise

import echo

from gui.qt.plugins.tileeditorview import Tile, Direction

from copy import deepcopy

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
        
        self.linearSpeed = 150
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
        if base.win.movePointer(0, base.win.getXSize()/2, 
                                base.win.getYSize()/2):
            self.node.setH(self.node.getH() -  (x - base.win.getXSize()/2)*0.3)
            base.camera.setP(base.camera.getP() - 
                             (y - base.win.getYSize()/2)*0.3)
        return task.cont

    def moveUpdate(self,task):
        """ this task makes the vcam move """
        # move where the keys set it
        self.node.setPos(self.node,self.walk * globalClock.getDt() \
                         * self.linearSpeed)
        self.node.setPos(self.node,self.strafe * globalClock.getDt() \
                         * self.linearSpeed)
        return task.cont

# TODO put in conf file ?
VERTEX_PER_ROW = 4

class TrackGenerator(DirectObject):   
    def __init__(self):
        self.isWireframe = False
        self.objectName = None
        
        self.accept("mouse1", self.grabPoint)
        self.accept("mouse1-up", self.releasePoint)
        self.accept("p", self.saveTo, ["/tmp/test.egg"])
        self.accept("b", self.toggleOobe)
        self.accept("r", self.toggleRenderMode)
        self.accept("escape", self.hideTrack)
        
        self.selectedObject = None
        self.points = []
        self.surface = None
        
        self._matrixIsTransposed = False
        self.tempVertexes = []
        
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
            self.pickerRay.setFromLens(base.camNode, mousePos.getX(), 
                                       mousePos.getY())
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
                nearPoint = render.getRelativePoint(camera, 
                                                self.pickerRay.getOrigin())
                nearVec = render.getRelativeVector(camera, 
                                               self.pickerRay.getDirection())
                pos = pointAtZ(0, nearPoint, nearVec)
                self.selectedObject.setPos(pos)
                
                v=self.surface.verts[int(self.selectedObject.getNetTag("idx"))]
                v["point"] = pos
                
                self.surface.recompute()
        
        return task.cont
        
    def saveTo(self, fileName):
        egg = self.surface.toEgg()
        egg.writeEgg(Filename(fileName))
    
    def generate(self, grid):
        self.tempVertexes = []
        self._matrixIsTransposed = False
        self.generateVertexes(grid)
        self.generateSurface(self.tempVertexes)
    

    def generateVertexes(self, grid, start=None, end=None, 
                         tileIndexStart=None, tileIndexEnd=None):
        # can't use a for loop since inside I'll change i, not a very good
        # design though...
        if start == None: start = 0
        if end == None: end = len(grid)
        if tileIndexStart == None: tileIndexStart = 0
        if tileIndexEnd == None: tileIndexEnd = len(grid[0])
        
        for i,r in enumerate(grid):
            for j,col in enumerate(r):
                if col is not None:
                    pass#print i,j, "|", col.y, col.x,col.direction
        
        while start < end:
            row = grid[start]
            """ 
            Read the whole row, detect the curves.
            Possible cases are: 
             - 12 : forward-left
             - 14 : forward-right
             - 21 : left-forward
             - 41 : right-forward
             - 121: forward-left-forward
             - 141: forward-right-forward
            """
            case = None
            tiles = filter(lambda x: x is not None, row[tileIndexStart:])
            if len(tiles) > 0:
                tileStr = "".join(map(lambda t: str(t.direction), tiles))
                if "12" in tileStr and "21" in tileStr:
                    logger.debug("Forward-Left-Forward detected")
                    idx = start
                    s = len(row) - row.index(tiles[tileStr.rfind("2")])
                    e = len(row) - row.index(tiles[tileStr.find("2")])
                    newGrid = rotateMatrixClockwise(grid)
                    self.generateVertexes(newGrid, s-1, e, idx)
                    
                    # find out where to restart
                    newEnd = 0
                    for col in newGrid[e-1]:
                        if col is not None and col.x > newEnd:
                            newEnd = col.x
                    
                    # I need to increase it by the width of the curve
                    start = int(newEnd) -1
                    continue
                    
                elif "21" in tileStr:
                    logger.debug("Curve left detected")
                    
                    idx = start
                    s = len(row) - row.index(tiles[tileStr.rfind("2")])
                    e = len(grid) # TODO probably wrong, try the one on flf
                    newGrid = rotateMatrixClockwise(grid)

                    self.generateVertexes(newGrid, s-1, e, idx)
                    break
                
                elif "14" in tileStr and "41" in tileStr:
                    s = row.index(tiles[tileStr.find("4")])
                    e = row.index(tiles[tileStr.rfind("4")])
                    idxStart = 0
                    newGrid = rotateMatrixAntiClockwise(grid)
                    # I need to reverse the columns otherwise vertexes are read
                    # from "down" to "top"
                    for r in newGrid:
                        r.reverse()
                    self.generateVertexes(newGrid,s,e+1,idxStart)
                    
                    # find latest column before the forward section begins
                    tile = tiles[tileStr.rfind("4")]
                    row = newGrid[int(tile.x)]
                    idx = 0
                    for col in row:
                        if col is not None and col.x > idx:
                            idx = col.x
                    
                    start = int(idx) +1
                    continue
                    
                elif "14" in tileStr:
                    logger.debug("Detected right curve")
                    s = row.index(tiles[tileStr.find("4")])
                    e = row.index(tiles[tileStr.rfind("4")])
                    idxStart = 0
                    idxEnd = len(row) - row.index(tiles[tileStr.find("4")])
                    newGrid = rotateMatrixAntiClockwise(grid)
                    # I need to reverse the columns otherwise vertexes are read
                    # from "down" to "top"
                    for r in newGrid:
                        r.reverse()
                    
                    self.generateVertexes(newGrid,s,e+1,idxStart)
                    break
                    
                else:
                    self.addVertexes(tiles, self.tempVertexes)
            else:
                pass
                
            start+=1
            
    
    def generateVertexes2(self, grid, x=0,y=0,z=0):
        """ this algorithm transpose the matrix """
        
        stepOut = False
        
        for i,row in enumerate(grid):
            for j,col in enumerate(row):
                # iterate the row until we find a column which is not None
                if col is not None:
                    tileRow = []
                    direction = col.direction
                    if direction == Direction.FORWARD or \
                        direction == Direction.RIGHT or \
                        (direction == Direction.LEFT and 
                         self._matrixIsTransposed):
                        
                        # read 5 (maximum number of tiles per row) +1 columns
                        tileRow = [grid[i][j+w] for w in range(5+1) 
                                   if (j+w) < 80]
                    elif direction == Direction.LEFT:
                        tileRow = [grid[i][w] for w in range(j,len(row)) 
                                   if (j+w) < 80]

                    tileRow = filter(lambda x: x is not None, tileRow)
                    
                    if len(tileRow) > 0:
                        # detect if there is a curve (direction changes)
                        mustTranspose = False
                        curveOffset = 0
                        
                        if direction == Direction.FORWARD or \
                        direction == Direction.RIGHT or \
                        (direction == Direction.LEFT and self._matrixIsTransposed):
                            firstDir = tileRow[0].direction
                            for tile in tileRow:
                                if tile.direction != firstDir:
                                    mustTranspose = True
                                    curveOffset = grid[i].index(tile)
                                    break
                                
                        elif direction == Direction.LEFT:
                            if self._matrixIsTransposed:
                               mustTranspose = False
                            else: 
                                mustTranspose = True
                                # find out where the curve starts (position of first
                                # forward tile)
                                curveOffset = 0
                                for tile in tileRow:
                                    if tile.direction == Direction.FORWARD:
                                        curveOffset = grid[i].index(tile)-1
                                        break
                        
                        if mustTranspose:
                            logger.debug("Detected a curve, direction is: %s" \
                                         % tile.direction)
                            
                            # TODO interpolate some vertexes to make the 
                            # curve smoother
                            
                            newgrid = deepcopy(grid)

                            # transpose matrix
                            if direction == Direction.FORWARD or \
                                direction == Direction.RIGHT :
                                newgrid = transpose2DMatrix(newgrid)[curveOffset:]
                            elif direction == Direction.LEFT:
                                newgrid = transpose2DMatrix(newgrid[i-1:])[:curveOffset]
                                newgrid.reverse()
                            
                            # call generate with the new matrix
                            self._matrixIsTransposed = True
                            self.generateVertexes(newgrid)
                            stepOut = True
                            #return
                            
                        else:
                            self.addVertexes(tileRow, self.tempVertexes)
                    # read another row
                    break       
            if stepOut:
                break
                    
    
    
    def addVertexes(self, tileRow, verts):                
        direction = tileRow[0].direction
        firstTile = tileRow[0]
        lastTile = tileRow[-1]
        if direction == Direction.FORWARD:
            xIncrement = (lastTile.x - firstTile.x+1) / float(VERTEX_PER_ROW)
            if len(tileRow) == 1:
                xIncrement = 1.0/ float(VERTEX_PER_ROW)
            for i in range(VERTEX_PER_ROW):
                x = firstTile.x + (i * xIncrement) + xIncrement/2.0
                y, z = firstTile.y, firstTile.z
                # FIXME
                type = self._colorForTile(tileRow[0].type)
                vert = {'node':None, 'point': (x,y,z), 
                                'type' : type}
                verts.append(vert)
               
        elif direction == Direction.RIGHT:
            yIncrement = (lastTile.y -firstTile.y) / float(VERTEX_PER_ROW)
            if len(tileRow) == 1:
                yIncrement = 1.0/ float(VERTEX_PER_ROW)
            
            offset = len(verts)
            for i in range(VERTEX_PER_ROW):
                y = firstTile.y + (i * yIncrement) + yIncrement/2.0
                x, z = firstTile.x, firstTile.z
                type = self._colorForTile(tileRow[0].type)
                vert = {'node':None, 'point': (x,y,z), 
                                'type' : type}
                verts.insert(offset,vert)
                
        elif direction == Direction.LEFT:
            direction = tileRow[0].direction
            firstTile = tileRow[0]
            lastTile = tileRow[-1]
            yIncrement = abs(lastTile.y -firstTile.y) / float(VERTEX_PER_ROW)
            if len(tileRow) == 1:
                yIncrement = 1.0/ float(VERTEX_PER_ROW)
            
            offset = len(verts)
            for i in range(VERTEX_PER_ROW):
                y = lastTile.y - (i * yIncrement) #- yIncrement/2.0
                x, z = firstTile.x, firstTile.z
                type = self._colorForTile(tileRow[0].type)
                vert = {'node':None, 'point': (x,y,z), 
                                'type' : type}
                verts.insert(offset,vert)
                
    def generateSurface(self, verts):
        logger.debug("Generating surface")
        
        for vert in verts:
            pass#print vert
        
        surface = Sheet("curve")
        surface.setup(4,4,VERTEX_PER_ROW, verts)
        surface.sheetNode.setNumUSubdiv(VERTEX_PER_ROW)
        surface.sheetNode.setNumVSubdiv(5)
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
        
#echo.echo_class(TrackGenerator)
