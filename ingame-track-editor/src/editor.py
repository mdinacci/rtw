# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("track-designer", INFO)

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject

from pandac.PandaModules import CollisionNode, CollisionHandlerQueue, \
CollisionTraverser, CollisionRay, GeomNode

from direct.gui.DirectGui import *

from mdlib.panda.input import InputManager
from mdlib.panda import utils

from pandac.PandaModules import CardMaker, Plane, Point3, Vec3, NodePath, \
PlaneNode, BitMask32, Filename, TextNode, Multifile

from grid import ThreeAxisGrid

import os

GROUND_Z = -3


def gridPosForPoint(point, offset=2.5):
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
    STRAIGHT = "../res/straight.egg"
    CURVE = "../res/curve.egg"
    MONSTER = "../res/diagonal.egg"


class ExportFrame(object):
    def __init__(self, exportCB):
        self._exportCallback = exportCB
        self._setupGUI()
    
    def show(self):
        self._frame.show()
        
    def hide(self):
        self._frame.hide()

    def _setupGUI(self):
        maps = loader.loadModel('../res/straight-button.egg')
                
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
        
        nameEntry = DirectEntry(text="", initialText="",
                             pos = (-.25, 0 , .35), cursorKeys=1, numLines = 1,
                             width=12,scale=.05, rolloverSound=None, 
                             clickSound=None)
        
        zOffset = 0.2
        for i in range(3):
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
        
        okButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.07,borderWidth=(0,0),
                     command=self._exportCallback, relief=None, text="Export",
                     rolloverSound=None, clickSound=None,pos = (0.3,0,-.30))
    
        cancelButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.07,borderWidth=(0,0),
                     command=self._cancelPressed, relief=None, pos = (0.5,0,-.30),
                     rolloverSound=None, clickSound=None,text="Cancel")
        
        nameEntry.reparentTo(frame)
        nameLabel.reparentTo(frame)
        goldLabel.reparentTo(frame)
        silverLabel.reparentTo(frame)
        bronzeLabel.reparentTo(frame)
        okButton.reparentTo(frame)
        cancelButton.reparentTo(frame)
        
        self._frame = frame
        self._frame.hide()
        
    def _cancelPressed(self):
        self._frame.hide()


class TrackEditor(object):
    def __init__(self):
        self._trackExporter = ExportFrame(self._exportTrack)
        
        self._setupInput()
        
        self._setupCamera()
        self._setupGUI()
        self._setupGround()
        self._setupCollision()
       
        self._lastPosition = Point3(0,0,0)
        
        # segment dragged by selecting with left button and moving the mouse
        self._segmentDragged = None
        
        # the segment hovered by the mouse cursor
        self._hoveredSegment = None
        
        self._hasSelection = False
        self._isHovering = False
        self._hasRightSelectedSegment = False
        
        # invisible node that follows the mouse. The current segment is attached
        # to this node
        self._mouseNode = render.attachNewNode("mouseNode")
        self._mouseNode.setScale(0.5)
        self._mouseNode.setPos(0,0,0)
       
        self._trackNode = render.attachNewNode("trackNode")
        self._trackNode.setScale(0.5)
        self._trackNode.setPos(0,0,0)
       
        self._tasks = []
        self._tasks.append(taskMgr.add(self._mouseTask, 'mouseTask'))
        self._tasks.append(taskMgr.add(self._inputTask, 'inputTask'))
        

    def _mouseTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
            
            if mpos.getX() > 0.95:
                camera.setX(camera.getX() +1)
            elif mpos.getX() < -0.95:
                camera.setX(camera.getX() -1)
            
            if mpos.getY() > 0.95:
                camera.setY(camera.getY() +1)
            elif mpos.getY() < -0.95:
                camera.setY(camera.getY() -1)
            
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
        self._inputMgr.bindCallback("mouse1-up", self._onMouseUp)
        self._inputMgr.bindCallback("mouse1-release", self._onMouseRelease)
        self._inputMgr.bindCallback("delete", self._deleteSegment)
        self._inputMgr.bindCallback("e", self._exportTrack)
        self._inputMgr.bindCallback("p", base.oobe)
        
    def _setupGround(self):
       cm = CardMaker("cm")
       cm.setFrame(-100, 100, -100, 100)
       self._ground = render.attachNewNode(cm.generate())
       self._ground.setPosHpr(0, 0, GROUND_Z-0.05, 0, -90, 0) 
       self._ground.setColor(0.4,0.6,0.8)
       grid = ThreeAxisGrid(zsize=0, gridstep=5, subdiv=2)
       gridNp = grid.create()
       gridNp.reparentTo(render)
       gridNp.setPos(2.5,0,GROUND_Z-.01)
       
       self._grid = gridNp
       
    def _setupCollision(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        #Attach that node to the camera since the ray will need to be positioned
        #relative to it
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        #Everything to be picked will use bit 1. This way if we were doing other
        #collision we could seperate it
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()               #Make our ray
        self.pickerNode.addSolid(self.pickerRay)      #Add it to the collision node
        
        self.picker.addCollider(self.pickerNP, self.pq)
        #self.picker.showCollisions(render)
        
    def _setupCamera(self):
        base.disableMouse()
        camera.setPosHpr(0, -70, 80, 0, -60, 0)

    def _setupGUI(self):
        
        bottomFrame = DirectFrame(frameColor=(0.6,0,0,0.5), borderWidth=(1,1))
        
        maps = loader.loadModel('../res/straight-button.egg')
        straightButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-1.0,0,-0.8),extraArgs=[Segment.STRAIGHT],
                     rolloverSound=None, clickSound=None,text="")
        
        straightButton.reparentTo(bottomFrame)
        
        maps = loader.loadModel('../res/curve-button.egg')
        curveButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-0.8,0,-0.8),extraArgs=[Segment.CURVE],
                     rolloverSound=None, clickSound=None,text="")
        
        curveButton.reparentTo(bottomFrame)
        
        diagonalButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._segmentPressed, relief=None, 
                     pos = (-0.6,0,-0.8),extraArgs=[Segment.MONSTER],
                     rolloverSound=None, clickSound=None,text="")
        
        diagonalButton.reparentTo(bottomFrame)
        
        exportButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._trackExporter.show, relief=None, 
                     pos = (0.9,0,0.9),
                     rolloverSound=None, clickSound=None,text="")
    
    def _segmentPressed(self, segmentType):
        if self._hasSelection:
            self._segmentDragged.removeNode()
            
        logger.debug("Creating a new %s" % segmentType)
        self._segmentDragged = loader.loadModel(segmentType)
        self._segmentDragged.reparentTo(self._mouseNode)
        self._segmentDragged.showTightBounds()
        
        segment = self._segmentDragged.find("**/segment*")
        segment.node().setIntoCollideMask(BitMask32.bit(1))
        
        self._hasSelection = True
        
    def _exportTrack(self):
        #exp = TrackExporter(self._trackNode)
        #exp.export()
        
        self._trackNode.setPos(0,0,0)
        self._trackNode.writeBamFile("/tmp/track.bam")
        
        mf = Multifile()
        mf.openWrite(Filename("/tmp/track.mf"))
        mf.addSubfile("track.bam", Filename("/tmp/track.bam"), 9)
        mf.close()
        
        self._trackExporter.hide()
        
        # TODO remove temp files.
        os.remove("/tmp/track.bam")
        
        
    def _deleteSegment(self):
        if self._isHovering:
            self._isHovering = False
            self._hoveredSegment.removeNode()
            self._hoveredSegment = None
    
    def _onShiftMouseClick(self):
        if self._isHovering:
            self._hoveredSegment = self._hoveredSegment.copyTo(self._trackNode)
            self._onMouseClick()
    
    def _onRMouseClick(self):    
        if self._isHovering:
            self._hoveredSegment.setH(self._hoveredSegment, 90)
        
    def _onMouseClick(self):
        if self._hasSelection:
            # put segment down
            pos = self._segmentDragged.getPos(render)
            self._segmentDragged.reparentTo(self._trackNode)
            self._segmentDragged.setPos(render, pos)
            self._segmentDragged.hideBounds()
            self._hoveredSegment = self._segmentDragged
            self._hasSelection = False
        else:
            # try to select a segment
            if self._hoveredSegment is not None:
                self._segmentDragged = self._hoveredSegment
                self._segmentDragged.showTightBounds()
                
                pos = self._segmentDragged.getPos(self._mouseNode)
                self._segmentDragged.reparentTo(self._mouseNode)
                self._segmentDragged.setPos(0,0,0)
                
                self._isHovering = False
                self._hasSelection = True
            
    
    def _onMouseUp(self):
        pass
    
    def _onMouseRelease(self):
        pass
        
    def destroy(self):
        for task in self._tasks:
            taskMgr.remove(task)
            
        self._trackNode.removeNode()
        self._mouseNode.removeNode()
        self._grid.removeNode()


if __name__ == '__main__':
    
    te = TrackEditor()

run()