# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("track-designer", DEBUG)

from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, \
CollisionTraverser, CollisionRay, GeomNode

from direct.gui.DirectGui import *

from mdlib.panda.input import InputManager
from mdlib.panda import utils

from pandac.PandaModules import CardMaker, Plane, Point3, Vec3, Vec4, NodePath,\
PlaneNode, BitMask32, Filename, TextNode, Multifile, RenderModeAttrib, \
TransparencyAttrib, LightAttrib, DirectionalLight, AmbientLight,\
VirtualFileSystem, AntialiasAttrib, CollisionNode, CollisionSphere
from grid import ThreeAxisGrid
from utils import strTimeToTenths
#from local import *

import os, shutil
from md5 import md5

from time import time

GROUND_Z = -3
START_POS = Point3(0, -37.5, -3)
TRACK_SCALE = 2.5

#font = loader.loadFont("cmss12")

def randomString():
    return "%s" % time()

def gridPosForPoint(point, offset=1.25):
    x = point.getX()
    y = point.getY()
    
    def getPoint(val):
        a = round(val / offset)
        b = round(val % offset)
        
        newVal = val
        if b == 0:
            pass
        elif b <= 2:
            newVal = a * offset
        else:
            newVal = a * offset
        return newVal
            
    return Point3(getPoint(x), getPoint(y), point.getZ())
        

class Segment:
    STRAIGHT = "straight.egg"
    CURVE = "curve.egg"
    DIAGONAL = "diagonal.egg"
    CHECKPOINT = "cp.egg"


class Item:
    ACCELERATE = "accelerate.egg"
    DECELERATE = "decelerate.egg"
    HOLE = "hole.egg"
    JUMP = "jump.egg"
    INVERT = "invert.egg"
    INVISIBLE = "bonus.egg"
    PLUSTHREE = "bonus.egg"
    MINUSTHREE = "bonus.egg"


class SegmentEditor(object):
    
    """ Edit a single segment by deleting tiles, adding bonuses etc... """
    
    def __init__(self, backCallback):
        self._backCallback = backCallback
        self._rootNode = render.attachNewNode("root-node")
        self._mouseNode = self._rootNode.attachNewNode("mouseNode")
       
        self._hasSelection = False # are we dragging an item ?
        self._segment = None
        self._tile = None # current tile hovered by the mouse cursor
        self._itemDragged = None # item currently dragged ?
        self._isHovering = False # is mouse over segment ?
        self._tileBounds = None
        
        self._setupInput()
        self._setupCollision()
        self._setupGUI()
    
    def restoreSegment(self):
        self._segment.reparentTo(self._segmentPrevParent)
        self._segment.setPos(self._segmentPrevPos)
        self._segment.setHpr(self._segmentPrevHpr)
        self._segment.setScale(1)
        
        return self._segment
           
    def destroy(self):
        self._frame.destroy()
        self._stopTasks()
        self._rootNode.removeNode()
        self.pickerNP.removeNode()
    
    def hide(self):
        self._frame.hide()
        self._stopTasks()
    
    def edit(self, segment):
        logger.debug("Editing segment: " % segment)
        self._faceCameraPosition(self._mouseNode, 40)
        
        self._setupTasks()
        
        self._segmentPrevParent = segment.getParent()
        self._segmentPrevPos = segment.getPos()
        self._segmentPrevHpr = segment.getHpr()
        
        self._faceCameraPosition(segment)
        
        self._segment = segment
        self._segmentCopy = self._segment.copyTo(NodePath("segment"))
        self._segmentCopy.hide()
        self._frame.show()
    
    def _faceCameraPosition(self, obj, distance=41):
        parent = obj.getParent()
        obj.reparentTo(base.camera)

        forward = base.camera.getQuat().getForward()
        forward.setZ(0)
        forward.normalize()
        forward *= distance # place it a bit far away from the camera
        obj.setPos(forward)
        obj.setHpr(base.camera.getHpr() * -1)
        
        obj.wrtReparentTo(parent)
        
    def _stopTasks(self):
        taskMgr.remove("update")
        taskMgr.remove("update-input")
    
    def _updateTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            
            if self._hasSelection:
                # Gets the point described by pickerRay.getOrigin(), which is 
                # relative to camera, relative instead to render
                nearPoint = render.getRelativePoint(camera, 
                                                    self.pickerRay.getOrigin())
                # Same thing with the direction of the ray
                nearVec = render.getRelativeVector(camera, 
                                               self.pickerRay.getDirection())
                
                pos = None
                if self._tile is not None:
                    pos = utils.pointAtZ(self._tile.getZ(render), nearPoint, nearVec)
                else:
                    pos = utils.pointAtZ(self._segment.getZ(render), nearPoint, nearVec)
                    
                self._mouseNode.setPos(pos)
            
            if self._segment is not None:
                self.picker.traverse(self._segment)
                if self.pq.getNumEntries() > 0:
                    self._isHovering = True
                    self.pq.sortEntries()
                    if self._tile is not None:
                        self._tileBounds.reset()
                    self._tile = self.pq.getEntry(0).getIntoNodePath()
                    # line are attached to the tile they describe
                    if self._tileBounds is not None:
                        self._tileBounds.removeNode()
                    self._tileBounds = utils.showGeometryLines(self._tile, 
                                                       self._tile.getParent(),
                                                       zOffset=0.1)
                else:
                    self._isHovering = False
                    if self._tile is not None:
                        self._tileBounds.removeNode()
                
        return task.cont
    
    def _setupCollision(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        #Attach that node to the camera since the ray will need to be positioned
        #relative to it
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(2))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
    
    def _setupInput(self):
        self._inputMgr = InputManager()
        self._inputMgr.createSchemeAndSwitch("segment-editor")
        self._inputMgr.bindCallback("mouse1", self._onMouseClick)
        self._inputMgr.bindCallback("delete", self._deleteTile)
        self._inputMgr.bindCallback("p", base.oobe)
        
    def _setupTasks(self):
        taskMgr.add(self._updateTask, "update")
        taskMgr.add(self._inputMgr.update, "update-input")
    
    def _setupGUI(self):
        font = loader.loadFont("cmss12")
        
        self._frame = DirectFrame()
        maps = loader.loadModel('../res/editor/straight-button.egg')
        
        bottomFrame = DirectFrame()
        bottomFrame.reparentTo(self._frame)
        backButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._backPressed, relief=None, pos = (1.0,0,-.9),
                     rolloverSound=None, clickSound=None,
                     text_font=font, text="Back")
        resetButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._resetPressed, relief=None, pos = (1.0,0,.9),
                     rolloverSound=None, clickSound=None,
                     text_font=font, text="Reset")
        
        backButton.reparentTo(self._frame)
        resetButton.reparentTo(self._frame)
        
        # controls
        maps = loader.loadModel(Item.ACCELERATE)
        accelButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None, pos = (-1.2,0,-.9),
                     rolloverSound=None, clickSound=None, text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.ACCELERATE],
                         text="Accelerate")
        maps = loader.loadModel(Item.DECELERATE)
        decelButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None, pos = (-0.8,0,-.9),
                     rolloverSound=None, clickSound=None, text_font=font, 
                     text_align=TextNode.ALeft, extraArgs=[Item.DECELERATE],
                     text="Decelerate")
        maps = loader.loadModel(Item.JUMP)
        jumpButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None, pos = (-0.4,0,-.9),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.JUMP],
                     text="Jump")
        """
        maps = loader.loadModel(Item.HOLE)
        holeButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._holePressed, relief=None, pos = (0,0,-.9),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, text="Hole")
        """
        maps = loader.loadModel(Item.INVERT)
        invertButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None,pos = (0.4,0,-.9),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.INVERT],
                     text="Invert")
        invisibleButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None,pos = (-1.2,0,.7),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.INVISIBLE],
                     text="Invisible")
        plusThreeButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None,pos = (-1.2,0,.55),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.PLUSTHREE],
                     text="+3 seconds")
        minusThreeButton = DirectButton(scale=.07,borderWidth=(0,0),
                     command=self._itemPressed, relief=None,pos = (-1.2,0,.40),
                     rolloverSound=None, clickSound=None,  text_font=font,
                     text_align=TextNode.ALeft, extraArgs=[Item.MINUSTHREE],
                     text="-3 seconds")
        
        accelButton.reparentTo(self._frame)
        decelButton.reparentTo(self._frame)
        jumpButton.reparentTo(self._frame)
        #holeButton.reparentTo(self._frame)
        invertButton.reparentTo(self._frame)
        invisibleButton.reparentTo(self._frame)
        plusThreeButton.reparentTo(self._frame)
        minusThreeButton.reparentTo(self._frame)
        self._frame.hide()
    
    def _backPressed(self):
        if self._tile is not None:
            self._tileBounds.reset()
        self._backCallback()
    
    def _holePressed(self):
        pass
    
    def _itemPressed(self, item):
        if self._hasSelection:
            self._itemDragged.removeNode()
            
        logger.debug("Creating a new %s" % item)
        self._itemDragged = loader.loadModel(item)
        self._itemDragged.reparentTo(self._mouseNode)
        # to float above the tile
        self._itemDragged.setZ(self._itemDragged.getZ()+.2) 
        self._itemDragged.setScale(2)
        
        self._itemDragged.node().setIntoCollideMask(BitMask32.bit(2))
        self._itemDragged.showTightBounds()
            
        self._hasSelection = True
    
    def _resetPressed(self):
        logger.debug("Resetting segment")
        
        parent = self._segment.getParent()
        self._segment.removeNode()
        self._segment = self._segmentCopy
        self._segment.reparentTo(parent)
        self._segment.show()
        
    def _deleteTile(self):
        if self._tile is not None:
            self._tile.removeNode()
            self._tileBounds.reset()
            self._tile = None
    
    def _onMouseClick(self):
        if self._hasSelection:
            if self._isHovering:
                logger.debug("Placing segment")    
                # put item down_mouseNode
                pos = self._itemDragged.getPos(render)
                self._itemDragged.wrtReparentTo(self._segment)
                self._itemDragged.hideBounds()
                self._hasSelection = False
        else:
            # select a tile
            pass

    
class ExportFrame(object):
    
    """ Export widget """
    
    def __init__(self, exportCB, cancelCB):
        self._exportCallback = exportCB
        self._cancelCallback = cancelCB
        
        self._setupGUI()
    
    def destroy(self):
        self._frame.destroy()
    
    def show(self):
        self._frame.show()
        
    def hide(self):
        self._frame.hide()
        
    def getTID(self):
        hash = md5()
        hash.update(self._nameEntry.get())
        return hash.hexdigest()
    
    def getTrackName(self):
        return self._nameEntry.get()
    
    def getMaximumTime(self):
        return self._getTime(self._times[3])
    
    def getGoldTime(self):
        return self._getTime(self._times[0])
    
    def getSilverTime(self):
        return self._getTime(self._times[1])
    
    def getBronzeTime(self):
        return self._getTime(self._times[2])

    def _getTime(self, time):
        mins = time[0].get()
        secs = time[1].get()
        tenths = time[2].get()
    
        return strTimeToTenths("%s:%s.%s" % (mins, secs, tenths))

    def _setupGUI(self):
        maps = loader.loadModel('../res/editor/straight-button.egg')
                
        frame = DirectFrame(frameColor=(.3,.3,.3,.3), frameSize=(-.5,.7,-.5,.5))
        
        nameLabel = DirectLabel(text="Name: ", scale=.05, pos=(-.45, 0, .35),
                                      relief=None, text_align=TextNode.ALeft)
        
        # Gold widgets
        goldLabel = DirectLabel(text="Gold: ", scale=.05, pos=(-.45, 0, .20),
                                      relief=None, text_align=TextNode.ALeft)
        # Silver widgets
        silverLabel = DirectLabel(text="Silver: ", scale=.05, pos=(-.45,0, .05),
                                      relief=None, text_align=TextNode.ALeft)
        
        bronzeLabel = DirectLabel(text="Bronze: ", scale=.05, pos=(-.45,0, -0.1),
                                      relief=None, text_align=TextNode.ALeft)
        
        limitLabel = DirectLabel(text="Limit: ", scale=.05, pos=(-.45,0, -0.25),
                                      relief=None, text_align=TextNode.ALeft)
        
        nameEntry = DirectEntry(text="", initialText="",
                             pos = (-.25, 0 , .35), cursorKeys=1, numLines = 1,
                             width=12,scale=.05, rolloverSound=None, 
                             clickSound=None)
        
        zOffset = 0.2
        self._times = []
        for i in range(4):
            
            aLabelMin = DirectLabel(text="Minutes: ",scale=.05, 
                                    pos=(-.25, 0, 0+zOffset),
                                    relief=None, text_align=TextNode.ALeft)
            aEntryMin = DirectEntry(text="", initialText="",
                         pos = (-.05, 0 , 0+zOffset), cursorKeys=1, numLines = 1,
                         width=1,scale=.05,rolloverSound=None, 
                         clickSound=None)
            aLabelSec = DirectLabel(text="Seconds: ",scale=.05, 
                       pos=(0.05, 0, 0+zOffset),relief=None, 
                       text_align=TextNode.ALeft)
            aEntrySec = DirectEntry(text="", initialText="",
                         pos = (0.25, 0 , 0+zOffset), cursorKeys=1, numLines = 1,
                         width=1,scale=.05,rolloverSound=None, clickSound=None)
            aLabelTenths = DirectLabel(text="Tenths: ",scale=.05, relief=None,
                          pos=(0.35, 0, 0+zOffset),text_align=TextNode.ALeft)
            aEntryTenths = DirectEntry(text="", initialText="",
                         pos = (0.52, 0 , 0+zOffset), cursorKeys=1, numLines = 1,
                         width=1,scale=.05,rolloverSound=None, clickSound=None)
            zOffset -= 0.15
            
            aLabelMin.reparentTo(frame)
            aEntryMin.reparentTo(frame)
            aLabelSec.reparentTo(frame)
            aEntrySec.reparentTo(frame)
            aLabelTenths.reparentTo(frame)
            aEntryTenths.reparentTo(frame)
            
            self._times.append((aEntryMin, aEntrySec, aEntryTenths))
        
        okButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.07,borderWidth=(0,0),
                     command=self._exportCallback, relief=None, text="Export",
                     rolloverSound=None, clickSound=None,pos = (0.3,0,-.40))
    
        cancelButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.07,borderWidth=(0,0),
                     command=self._cancelCallback, relief=None, pos = (0.5,0,-.40),
                     rolloverSound=None, clickSound=None,text="Cancel")
        
        nameEntry.reparentTo(frame)
        self._nameEntry = nameEntry
        
        nameLabel.reparentTo(frame)
        goldLabel.reparentTo(frame)
        silverLabel.reparentTo(frame)
        bronzeLabel.reparentTo(frame)
        limitLabel.reparentTo(frame)
        okButton.reparentTo(frame)
        cancelButton.reparentTo(frame)
        
        self._frame = frame
        self._frame.hide()
        

class TrackEditor(object):
    
    """ Create the track """
    
    name = "track-designer"
    
    def __init__(self, screenMgr):
        self._screenMgr = screenMgr
        
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount("../res/editor/track-editor.bin", ".", VirtualFileSystem.MFReadOnly)
        
        self._trackExporter = ExportFrame(self._exportTrack, self._cancelExport)
        self._segmentEditor = SegmentEditor(self._editSegmentFinished)
        
        self._lastPosition = Point3(0,0,0)
        
        # segment dragged by selecting with left button and moving the mouse
        self._segmentDragged = None
        
        # the segment hovered by the mouse cursor
        self._hoveredSegment = None
        
        # current exported segment
        self._exportedSegment = None
        
        self._hasSelection = False
        self._isHovering = False
        self._hasRightSelectedSegment = False
        
        self._rootNode = render.attachNewNode("rootNode")
        # invisible node that follows the mouse. The current segment is attached
        # to this node
        self._mouseNode = self._rootNode.attachNewNode("mouseNode")
        self._mouseNode.setScale(0.5)
        self._mouseNode.setPos(0,0,0)
        
        self._trackNode = self._rootNode.attachNewNode("trackNode")
        self._trackNode.setScale(0.5)
        self._trackNode.setPos(0,0,0)
        self._trackNode.setAntialias(AntialiasAttrib.MLine)
        
        self._cpsNode = self._rootNode.attachNewNode("checkpoints")
        self._cpsNode.setScale(0.5)
        self._cpsNode.setPos(0,0,0)
        self._cpsNode.setAntialias(AntialiasAttrib.MLine)
        #bonus = NodePath("bonus")
        #special = NodePath("special")
        #other = NodePath("track")
        
        self._setupInput()
        self._setupCamera()
        self._setupLights()
        self._setupGUI()
        self._setupGround()
        self._setupCollision()
        self._setupTasks()
    
    def _editSegment(self):
        if not self._isStartingSegment(self._hoveredSegment):
            self._hoveredSegment.setColor(1,1,1)
            self._stopTasks()
            self._gui.hide()
            self._segmentEditor.edit(self._hoveredSegment)
    
    def _editSegmentFinished(self):
        self._segmentEditor.hide()
        segment = self._segmentEditor.restoreSegment()
        # necessary because if the segment has been reset in the segment editor,
        # hoveredSegment holds a reference to a zombie node 
        self._hoveredSegment = segment
        self._gui.show()
        self._setupTasks()
     
    def _setupTasks(self):
        self._tasks = []
        self._tasks.append(taskMgr.add(self._mouseTask, 'mouseTask'))
        self._tasks.append(taskMgr.add(self._inputTask, 'inputTask'))
    
    def _mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            
            # move the camera if the mouse is close to the edges
            if mpos.getX() > 0.95:
                camera.setX(camera.getX() +.5)
            elif mpos.getX() < -0.95:
                camera.setX(camera.getX() -.5)
            
            if mpos.getY() > 0.95:
                camera.setY(camera.getY() +.5)
            elif mpos.getY() < -0.95:
                camera.setY(camera.getY() -.5)
            
            if self._hasSelection:
                # Gets the point described by pickerRay.getOrigin(), which is 
                # relative to camera, relative instead to render
                nearPoint = render.getRelativePoint(camera, 
                                                    self.pickerRay.getOrigin())
                # Same thing with the direction of the ray
                nearVec = render.getRelativeVector(camera, 
                                               self.pickerRay.getDirection())
                
                pos = gridPosForPoint(utils.pointAtZ(GROUND_Z, nearPoint, nearVec))
                self._mouseNode.setPos(pos)
                    
            self.picker.traverse(self._trackNode)
            if self.pq.getNumEntries() > 0:
                self.pq.sortEntries()
                contact = self.pq.getEntry(0).getIntoNodePath()
                
                if self._hoveredSegment is not None:
                    self._hoveredSegment.setColor(1,1,1)
                
                self._hoveredSegment = contact.getParent().getParent()
                self._hoveredSegment.setColor(1,1,0)
                self._isHovering = True
            else:
                self._isHovering = False
                if self._hoveredSegment is not None:
                    self._hoveredSegment.setColor(1,1,1)
            
        return task.cont
    
    def _inputTask(self, task):
        return self._inputMgr.update(task)
    
    def _setupInput(self):
        self._inputMgr = InputManager()
        self._inputMgr.createSchemeAndSwitch("editor")
        self._inputMgr.bindCallback("shift-mouse1", self._onShiftMouseClick)
        self._inputMgr.bindCallback("mouse1", self._onMouseClick)
        self._inputMgr.bindCallback("mouse3", self._onRMouseClick)
        self._inputMgr.bindCallback("delete", self._deleteSegment)
        
        self._inputMgr.bindCallback("e", self._editSegment)
        self._inputMgr.bindCallback("p", base.oobe)
        self._inputMgr.bindCallback("o", self._showCollisions)
        
        self._showingCollNodes = False
    
    def _showCollisions(self):
        if self._showingCollNodes:
            self._rootNode.find("**/copy").removeNode()
        else:
            t = self._trackNode.copyTo(NodePath("copy"))
            copy = self._rootNode.attachNewNode("copy")
            t.reparentTo(copy)
            
            segs = t.findAllMatches("**/segment*")
            for seg in segs:
                fromMask = BitMask32.allOff()
                intoMask = BitMask32.allOff()
                
                center = seg.getBounds().getCenter()
                p = seg.getPos(render)# + (seg.getBounds().getCenter()*.5)
                np = seg.attachCollisionSphere("cs", p.getX(), p.getY(),p.getZ(),
                                               seg.getBounds().getRadius()/2.0,
                                               fromMask, intoMask)
                np.show()
                np.showBounds()
                np.reparentTo(copy)
                
        self._showingCollNodes = not self._showingCollNodes
    
    def _setupGround(self):
        # All the "magic" numbers are there to prevent z-fighting
        cm = CardMaker("cm")
        cm.setFrame(-100, 100, -100, 100)
        self._ground = self._rootNode.attachNewNode(cm.generate())
        self._ground.setPosHpr(0, 0, GROUND_Z-1.1, 0, -90.1, 0) 
        self._ground.setColor(0.4,0.6,0.8)
        grid = ThreeAxisGrid(zsize=0, gridstep=5, subdiv=2)
        gridNp = grid.create()
        gridNp.reparentTo(self._rootNode)
        gridNp.setPosHpr(2.5,0,GROUND_Z -.02,0, 0.1, 0)
        gridNp.setAntialias(AntialiasAttrib.MLine)
        
        gridNp.setP(gridNp.getP()+.1)
        gridNp.flattenStrong()
       
        self._grid = gridNp
        
        # load the initial segment
        segment = loader.loadModel(Segment.STRAIGHT)
        segment.reparentTo(self._trackNode)
        segment.setPos(self._rootNode,START_POS)
        tiles = segment.findAllMatches("**/tile*")
        for tile in tiles:
            tile.node().setIntoCollideMask(BitMask32.bit(2))
            
        pos = "%d,%d,%d" % (segment.getX(), segment.getY(), segment.getZ())
        segment.setTag("start-point", pos)
        segment.setTag("id", randomString())
       
    def _setupCollision(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        #Attach that node to the camera since the ray will need to be positioned
        #relative to it
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNP.show()
        #Everything to be picked will use bit 1. This way if we were doing other
        #collision we could separate it
        self.pickerNode.setFromCollideMask(BitMask32.bit(2))
        self.pickerRay = CollisionRay()               #Make our ray
        self.pickerNode.addSolid(self.pickerRay)      #Add it to the collision node
        
        self.picker.addCollider(self.pickerNP, self.pq)
        
    def _setupCamera(self):
        base.disableMouse()
        camera.setPosHpr(0, -70, 80, 0, -60, 0)

    def _setupLights(self):
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(.4, .4, .4, 1) )
        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setDirection( Vec3( 0, 0, GROUND_Z ) )
        directionalLight.setColor( Vec4( 0.9, 0.9, 0.9, 1 ) )
        dnp = self._rootNode.attachNewNode(directionalLight)
        anp = self._rootNode.attachNewNode(ambientLight)
        
        self._trackNode.setLight(dnp)
        self._trackNode.setLight(anp)
    
    def _setupGUI(self):
        font = loader.loadFont("cmss12")
        
        self._gui = DirectFrame(text_font=font)
        
        bottomFrame = DirectFrame(frameColor=(0.6,0,0,0.5), borderWidth=(1,1))
        
        maps = loader.loadModel('../res/editor/straight-button.egg')
        straightButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-1.1,0,-0.9),extraArgs=[Segment.STRAIGHT],
                     rolloverSound=None, clickSound=None, text_font=font,
                     text="Straight", text_scale=0.7)
        
        straightButton.reparentTo(bottomFrame)
        
        maps = loader.loadModel('../res/editor/curve-button.egg')
        curveButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-0.8,0,-0.9),extraArgs=[Segment.CURVE],
                     rolloverSound=None, clickSound=None,text_font=font,
                     text="Curve", text_scale=0.7)
        
        curveButton.reparentTo(bottomFrame)
        
        diagonalButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-0.5,0,-0.9),extraArgs=[Segment.DIAGONAL],
                     rolloverSound=None, clickSound=None,text_font=font,
                     text="Diagonal", text_scale=0.7)
        
        diagonalButton.reparentTo(bottomFrame)
        
        checkpointButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-0.1,0,-0.9),extraArgs=[Segment.CHECKPOINT],
                     rolloverSound=None, clickSound=None,text_font=font,
                     text="CP", text_scale=0.7)
        
        checkpointButton.reparentTo(bottomFrame)
        
        backButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._backPressed, relief=None, 
                     pos = (1,0,-0.9), text_scale=0.7,
                     rolloverSound=None, clickSound=None, text_font=font,
                     text="Back")
        
        exportButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._exportPressed, relief=None, 
                     pos = (0.85,0,0.9), text_scale=0.7,
                     rolloverSound=None, clickSound=None, text_font=font,
                     text="Export")
        
        previewButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._exportPressed, relief=None, 
                     pos = (1.1,0,0.9), text_scale=0.7,
                     rolloverSound=None, clickSound=None, text_font=font,
                     text="Preview")
        
        backButton.reparentTo(self._gui)
        exportButton.reparentTo(self._gui)
        previewButton.reparentTo(self._gui)
        bottomFrame.reparentTo(self._gui)
    
    def _stopTasks(self):
        for task in self._tasks:
            taskMgr.remove(task)
    
    def _backPressed(self):
        self._screenMgr.displayPreviousScreen()
    
    def _exportPressed(self):
        self._stopTasks()
        self._trackExporter.show()
    
    def _segmentPressed(self, segmentType):
        if self._hasSelection:
            self._segmentDragged.removeNode()
            
        logger.debug("Creating a new %s" % segmentType)
        self._segmentDragged = loader.loadModel(segmentType)
        self._segmentDragged.reparentTo(self._mouseNode)
        #self._segmentDragged.setTexture(loader.loadTexture("../res/editor/neutral.jpg"))
        self._segmentDragged.showTightBounds()
        
        tiles = self._segmentDragged.findAllMatches("**/tile*")
        for tile in tiles:
            tile.node().setIntoCollideMask(BitMask32.bit(2))
            
        self._hasSelection = True
    
    def _cancelExport(self):
        self._trackExporter.hide()
        self._setupTasks()
    
    def _reorderTrack(self, current, oldParent, parent):
        def clear(node):
            node.clearPythonTag("seg")
            
        self._currentID = current.getNetTag("id")
        
        current.setName("segment-%d" % parent.getNumChildren())
        current.getParent().copyTo(parent)
                
        collTrav = CollisionTraverser()
        queue = CollisionHandlerQueue()
        
        # just in case the track is exported multiple times
        spheres = self._rootNode.find("**/spheres")
        if not spheres.isEmpty():
            spheres.removeChildren()
            
        spheres = self._rootNode.attachNewNode("spheres")
        
        segs = oldParent.findAllMatches("**/segment*")
        for seg in segs:
            fromMask = BitMask32.allOff()
            intoMask = BitMask32(1)
            
            # check if seg is equal to current, in that case set the coll node  
            # as the "from" object.
            if seg.getNetTag("id") == current.getNetTag("id"):
                logger.debug("Setting collision masks for current segment %s" % seg.getNetTag("id"))
                fromMask = intoMask
                intoMask = BitMask32.allOff()
            
            center = seg.getBounds().getCenter()
            p = seg.getPos(render)# + (seg.getBounds().getCenter()*.5)
            np = seg.attachCollisionSphere("cs", p.getX(), p.getY(),p.getZ(),
                                           seg.getBounds().getRadius()/2.0,
                                           fromMask, intoMask)
            np.setPythonTag("seg", seg)
            np.reparentTo(spheres)
            collTrav.addCollider(np, queue)
        
        nextSegment = None
        
        collTrav.traverse(spheres)
        entries = queue.getNumEntries()
        into = None
        if entries > 0:
            if entries > 2: 
                # TODO alert user
                logger.error("Two collisions with new segments detected")
                import sys
                sys.exit(1)
            
            logger.debug("%d collisions " % entries)
            
            for i in range(entries):
                entry = queue.getEntry(i)
                into = entry.getIntoNodePath()
                
                nextSegment = into.getPythonTag("seg")
                logger.debug("Collision with new segment %s " % nextSegment)
                    
            current.getParent().removeNode()
        
        if nextSegment is not None:
            self._reorderTrack(nextSegment, oldParent, parent)
        else:
            if entries > 0:
                clear(into)
        
    
    def _exportTrack(self):
        exportNode = NodePath("track")

        # I need to work on a copy otherwise after flattening the track
        # it becomes impossible to edit the tiles.
        cps = self._cpsNode.copyTo(NodePath("checkpoints"))
        trackCopy = self._trackNode.copyTo(NodePath("track"))
        
        # reorder segments
        track = NodePath("track")
        self._reorderTrack(trackCopy.find("**/=start-point").find("**/segment"), 
                           trackCopy, track)
        
        track.setScale(TRACK_SCALE)
        track.reparentTo(exportNode)
        
        cps.setScale(TRACK_SCALE)
        cps.reparentTo(exportNode)
        
        exportNode.setPos(self._rootNode, 0,0,0)
        exportNode.setColorOff()
        
        lastSegment = track.getChild(track.getNumChildren()-1)
        pos = "%d,%d,%d" % (lastSegment.getX(), lastSegment.getY(), 
                            lastSegment.getZ())
        lastSegment.setTag("end-point", pos)
        
        track.flattenStrong()
        exportNode.writeBamFile("/tmp/track.bam")
        exportNode.ls()
        
        # export prc file
        f = open("/tmp/track.prc", "w")
        f.write("tid %s\n" % self._trackExporter.getTID())
        f.write("name %s\n" % self._trackExporter.getTrackName())
        f.write("gold %s\n" % self._trackExporter.getGoldTime())
        f.write("silver %s\n" % self._trackExporter.getSilverTime())
        f.write("bronze %s\n" % self._trackExporter.getGoldTime())
        f.close()

        # pack everything
        shutil.copy("../res/editor/ts.bin", "/tmp/track.bin")
        mf = Multifile()
        mf.openReadWrite(Filename("/tmp/track.bin"))
        mf.addSubfile("track.bam", Filename("/tmp/track.bam"), 9)
        mf.addSubfile("track.prc", Filename("/tmp/track.prc"), 9)
        mf.repack()
        mf.close()
        
        self._trackExporter.hide()
        
        os.remove("/tmp/track.bam")
        os.remove("/tmp/track.prc")
        
        # restore tasks
        self._setupTasks()
        
    def _isStartingSegment(self, segment):
        return segment.hasTag("start-point")
    
    def _deleteSegment(self):
        if self._isHovering:
            if not self._isStartingSegment(self._hoveredSegment):
                logger.debug("Deleting segment")    
                self._isHovering = False
                self._hoveredSegment.removeNode()
                self._hoveredSegment = None
    
    def _onShiftMouseClick(self):
        if self._isHovering:
            if not self._isStartingSegment(self._hoveredSegment):
                logger.debug("Duplicating segment")    
                self._hoveredSegment = self._hoveredSegment.copyTo(self._trackNode)
                self._onMouseClick()
    
    def _onRMouseClick(self):
        if self._isHovering:
            logger.debug("Rotating segment")    
            self._hoveredSegment.setH(self._hoveredSegment, 45)
        
    def _onMouseClick(self):
        if self._hasSelection:
            logger.debug("Placing segment")
            
            if not self._isHovering:
                # put segment down
                pos = self._segmentDragged.getPos(self._rootNode)
                if self._segmentDragged.getName().startswith("cp"):
                    self._segmentDragged.reparentTo(self._cpsNode)
                else:
                    self._segmentDragged.reparentTo(self._trackNode)
                self._segmentDragged.setPos(self._rootNode, pos)
                self._segmentDragged.hideBounds()
                self._hoveredSegment = self._segmentDragged
                self._hasSelection = False
                
                self._segmentDragged.setTag("id", randomString())
        else:
            # try to select a segment
            if self._isHovering:
                logger.debug("Selecting segment")    
                self._segmentDragged = self._hoveredSegment
                self._segmentDragged.showTightBounds()
                
                pos = self._segmentDragged.getPos(self._mouseNode)
                self._segmentDragged.reparentTo(self._mouseNode)
                self._segmentDragged.setPos(0,0,0)
                
                self._isHovering = False
                self._hasSelection = True
            
    def destroy(self):
        self._stopTasks()
        
        self._rootNode.clearLight()
        self._rootNode.removeNode()
        self.pickerNP.removeNode()
        
        self._trackExporter.destroy()
        self._segmentEditor.destroy()
        
        self._gui.destroy()

if __name__ == '__main__':
    import direct.directbase.DirectStart

    te = TrackEditor()

    run()