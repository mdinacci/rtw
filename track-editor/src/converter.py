#!/usr/bin/python
# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import *
loadPrcFile("../res/Config.prc")

from pandac.PandaModules import Point3, NodePath, TransparencyAttrib, \
        CullFaceAttrib, CardMaker, ModelNode
from mdlib.panda.data import ResourceLoader

__all__ = ["convert"]

rl = ResourceLoader()
cm = CardMaker("cm") 
directionX = 0
directionY = 1

TILE_TYPES = ("A","J","S", "F")
ITEM_TYPES = ("M","I","+","-", "?")

GLOBAL_SCALE = 5
STRAIGHT_SEGMENT_WIDTH = 10  * GLOBAL_SCALE
CURVE_SEGMENT_WIDTH = 15 *  GLOBAL_SCALE

class InvalidTrackLayoutException(Exception):
    pass


def applyEffect(tileType, tileNode, parent):
    newPos = tileNode.getPos(parent)
    newPos.setZ(newPos.getZ()+1.3)
    
    model = rl.loadModel("point.egg", pos=newPos)
    model.reparentTo(parent)
    name = "%s-%s" % (model.getName(), tileNode.getName())
    model.setName(name)
    model.setScale(.3)
    model.flattenStrong()
    
    print "adding item %s to %s at pos %s" % (tileType, tileNode, newPos) 
    
    if tileType == "M" :
        model.setTag("effect","M")
    elif tileType == "I":
        model.setTag("effect","I")
    elif tileType == "+":
        model.setTag("effect","+")
    elif tileType == "-":
        model.setTag("effect","-")
    elif tileType == "?":
        model.setTag("effect","?")
    
def modelPathForType(type):
    path = ""
    if type == 0:
        #path = "s.egg"
        path = "straight.egg"
    elif type == 1:
        path = "curve-right.egg"
    elif type == 2:
        path = "curve-left.egg"
    elif type == 3:
        path = "curve-right-down.egg"
    elif type == 4:
        path = "curve-left-down.egg"
    elif type == 7:
        path = "curve-right-left-up.egg"
    
    return path
    
def posForType(currentPos, prevType, type):
    global directionX, directionY
    
    newPos = Point3(0,0,0)
    # straight-straigt
    if prevType == 0 and type == 0:
        newPos += Point3(STRAIGHT_SEGMENT_WIDTH*directionX, 
                         STRAIGHT_SEGMENT_WIDTH * directionY, 
                         0)
        
    # straight-curve right
    elif prevType == 0 and type == 1:
        newPos += Point3(STRAIGHT_SEGMENT_WIDTH * directionX, 
                         STRAIGHT_SEGMENT_WIDTH * directionY, 0)
    
    # straight-curve left
    elif prevType == 0 and type == 2:
        newPos += Point3(STRAIGHT_SEGMENT_WIDTH * directionX, 
                         STRAIGHT_SEGMENT_WIDTH*directionY,0)
        directionY = -1
    
    # straight-curve left down
    elif prevType == 0 and type == 3:
        newPos += Point3(0, CURVE_SEGMENT_WIDTH*directionY,0)
        directionX = -1
        
    # straight-curve right down
    elif prevType == 0 and type == 4:
        newPos += Point3(0, CURVE_SEGMENT_WIDTH*directionY,0)
    
    # curve right-straight
    elif prevType == 1 and type == 0:
        newPos += Point3(CURVE_SEGMENT_WIDTH, CURVE_SEGMENT_WIDTH/2.0, 0)
    
    elif prevType == 1 and type == 1:
        raise InvalidTrackLayoutException("0 followed by 1")
    
    # curve right-curve left
    elif prevType == 1 and type == 2:
        newPos += Point3(CURVE_SEGMENT_WIDTH, 0, 0)
        directionY = -1  
        
    elif prevType == 1 and type == 3:
        pass
    
    elif prevType == 1 and type == 4:
        raise InvalidTrackLayoutException("0 followed by 1")
    
        
    # curve left-straight
    elif prevType == 2 and type == 0:
        newPos += Point3(CURVE_SEGMENT_WIDTH/3.0, STRAIGHT_SEGMENT_WIDTH*directionY, 0)
        
    # curve right down-curve left down
    elif prevType == 3 and type == 4:
        newPos += Point3(directionX*(CURVE_SEGMENT_WIDTH+25),0,0)
    
    elif prevType == 4 and type == 0:
        newPos += Point3(0, CURVE_SEGMENT_WIDTH*directionY, 0)
        
    elif prevType == 3 and type == 0:
        newPos += Point3(CURVE_SEGMENT_WIDTH*directionX,0, 0)
        directionY = 0
    
    """
    # straight-chicane right
    elif prevType == 0 and type == 7:
        if direction == 1:
            newPos += Point3(0,30*direction,0)
        elif direction == -1:
            newPos += Point3(-15,30*direction,0)
    # chicane right - straight
    elif prevType == 7 and type == 0:
        if direction == 1:
            newPos += Point3(15*direction,30*direction,0)
        elif direction == -1:
            newPos += Point3(0,30*direction,0)
    """
    
    return currentPos + newPos


def applyModel(tileType, tileNode, parent):
    if tileType == "N":
        pass
    else:
        plane = parent.attachNewNode(cm.generate())
        
        plane.setP(-90)
        plane.setPos(tileNode, -2.5, -2.5, .8)
        plane.setScale(5.2)
        plane.setTransparency(TransparencyAttrib.MAlpha)

        applyTexture(tileType, plane)
        
        plane.setTag("type", tileType)
        plane.setName(tileType)
    
def applyColor(tileType, tileNode):
    
    if tileType == "N":
        tileNode.setColor(1,1,1)
    if tileType == "A":
        tileNode.setColor(0,1,0)
    elif tileType == "J":
        tileNode.setColor(0,0,1)
    elif tileType == "S":
        tileNode.setColor(1,0,0)
    elif tileType == "F":
        tileNode.setColor(1,1,0.5)
    else:
        return
    if tileType == "N":
        tileNode.setColor(1,1,1)
    if tileType == "A":
        tileNode.setColor(0,1,0)
    elif tileType == "J":
        tileNode.setColor(0,0,1)
    elif tileType == "S":
        tileNode.setColor(1,0,0)
    elif tileType == "F":
        tileNode.setColor(1,1,0.5)
    else:
        return

    
def applyTexture(tileType, tileNode):
    
    tex = None
    if tileType == "N":
        tex = rl.loadTexture("neutral.jpg")
    elif tileType == "A":
        tex = rl.loadTexture("accelerate.png")
    elif tileType == "J":
        tex = rl.loadTexture("jump.png")
    elif tileType == "S":
        tex = rl.loadTexture("slow.jpg")
    elif tileType == "F":
        tex = rl.loadTexture("freeze.jpg")
    else:
        return
    
    # disable mipmapping
    #tex.setMinfilter(Texture.FTNearest)
    #tex.setMagfilter(Texture.FTNearest)
    
    tex.setMagfilter(Texture.FTLinear)
    tex.setMinfilter(Texture.FTLinearMipmapLinear)
    tex.setWrapU(Texture.WMClamp)
    tex.setWrapV(Texture.WMClamp)
    #tex.setBorderColor(VBase4(0.0, 0.0, 0, 1))

    ts = TextureStage('ts')
    ts.setMode(TextureStage.MModulate)
    
    tileNode.setTexture(ts, tex)
    

def cmpTiles(first, second):
    first = first.getName()
    second = second.getName()
    colFirst = first[first.rindex("-"):first.rindex(".")]
    rowFirst = first[first.rindex("."):]
    
    colSecond = second[second.rindex("-"):second.rindex(".")]
    rowSecond = second[second.rindex("."):]
    
    if rowFirst > rowSecond:
        return 1
    elif rowFirst < rowSecond:
        return -1
    else:
        if colFirst > colSecond:
            return 1
        elif colFirst < colSecond:
            return -1
        else:
            print "Comparing the same tile !!"
            return 0


def convert(track, outputFile):
    
    trackNode = NodePath("track")
    tilesRoot = NodePath("tiles")
    itemsRoot = NodePath("items")
    
    tilesRoot.reparentTo(trackNode)
    itemsRoot.reparentTo(trackNode)
    
    track = __import__(track).track
    
    prevType = None
    pos = Point3(0,0,0)
    
    for i, segment in enumerate(track):
        type = segment["type"]
        path = modelPathForType(type)
        pos = posForType(pos, prevType, type) 
        np = rl.loadModelAndReparent(path, tilesRoot, GLOBAL_SCALE, pos, noCache=True)
        segmentName = "%s@%d" % (np.getName(), i)
        np.setName(segmentName)
        
        if segment.has_key("checkpoint"):
            np.setTag("checkpoint", "1")
        
        applyTexture("N", np)
        #applyColor("N", np)
        
        tiles = segment["tiles"]
        geomTiles = np.findAllMatches("**/tile*").asList()
        #geomTiles.sort(cmp = cmpTiles)
        
        tilesTuple = zip(tiles, geomTiles)
        for tileType, tileNode in tilesTuple:
            
            tileNode.hide()
            
            if tileType == "H":
                tileNode.removeNode()
            elif tileType in TILE_TYPES:
                applyModel(tileType, tileNode, itemsRoot)
                #applyTexture(tileType, tileNode)
                #applyColor(tileType, tileNode)
            elif tileType in ITEM_TYPES:
                applyEffect(tileType, tileNode, itemsRoot)
                
        
        prevType = type
    
    # add endpoint to last segment
    np.setTag("endpoint", "1")
    
    itemsRoot.flattenStrong()

    trackNode.writeBamFile(outputFile)
    
    
if __name__ == '__main__':
    from sys import argv, path
    
    path.append("/home/mdinacci/Work/MD/rtw/track-editor/res/maps")
    
    map = "test_1"
    output = "/home/mdinacci/Work/MD/rtw/track-editor/res/models/track.bam"
    
    convert(map, output)
    
    from subprocess import Popen
    
    cmd = "pview %s" % output
    Popen(cmd.split())
    
    print "Finished."

    
