#!/usr/bin/python
# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import *
loadPrcFile("../res/Config.prc")

from pandac.PandaModules import Point3, NodePath, CullFaceAttrib
from mdlib.panda.data import ResourceLoader

__all__ = ["convert"]

rl = ResourceLoader()
direction = 1

TILE_TYPES = ("A","J","S", "F")
ITEM_TYPES = ("M","I","+","-", "?")

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
    global direction
    
    newPos = Point3(0,0,0)
    # straight-straigt
    if prevType == 0 and type == 0:
        newPos += Point3(0, 30*direction, 0)
    # straight-curve right
    elif prevType == 0 and type == 1:
        newPos += Point3(0, 30*direction, 0)
    # curve right-curve left
    elif prevType == 1 and type == 2:
        newPos += Point3(55.1, 0, 0)
        direction = -1
    # curve left-straight
    elif prevType == 2 and type == 0:
        newPos += Point3(5.85, 0, 0)
    # straight-curve right down
    elif prevType == 0 and type == 3:
        newPos += Point3(-27.4,27.55*direction,0)
    # curve right down-curve left down
    elif prevType == 3 and type == 4:
        newPos += Point3(41.68,0,0)
    elif prevType == 4 and type == 0:
        direction = 1
        newPos += Point3(-75.7,27.5,0)
    
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

    return currentPos + newPos


def applyColor(tileType, tileNode):
    
    if tileType == "N":
        tileNode.setColor(0,0,0)
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
        tex = rl.loadTexture("accelerate.jpg")
    elif tileType == "J":
        tex = rl.loadTexture("jump.jpg")
    elif tileType == "S":
        tex = rl.loadTexture("slow.jpg")
    elif tileType == "F":
        tex = rl.loadTexture("freeze.png")
    else:
        return
    
    # disable mipmapping
    #tex.setMinfilter(Texture.FTNearest)
    #tex.setMagfilter(Texture.FTNearest)
    
    tex.setMagfilter(Texture.FTLinear)
    tex.setMinfilter(Texture.FTLinearMipmapLinear)
    
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
    
    scale = 1
    prevType = None
    pos = Point3(0,0,0)
    
    for i, segment in enumerate(track):
        type = segment["type"]
        path = modelPathForType(type)
        pos = posForType(pos, prevType, type) 
        np = rl.loadModelAndReparent(path, tilesRoot, scale, pos, noCache=True)
        segmentName = "%s@%d" % (np.getName(), i)
        np.setName(segmentName)
        
        #applyTexture("N", np)
        
        tiles = segment["tiles"]
        geomTiles = np.findAllMatches("**/tile*").asList()
        geomTiles.sort(cmp = cmpTiles)
        
        tilesTuple = zip(tiles, geomTiles)
        for tileType, tileNode in tilesTuple:
            if tileType == "H":
                tileNode.removeNode()
            elif tileType in TILE_TYPES:
                #applyTexture(tileType, tileNode)
                applyColor(tileType, tileNode)
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
    
    map = "map_simple"
    output = "/home/mdinacci/Work/MD/rtw/track-editor/res/models/track.bam"
    
    convert(map, output)
    
    print "Finished."

    
