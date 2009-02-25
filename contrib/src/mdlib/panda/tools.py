# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import EggData, EggGroup, Filename
from subprocess import Popen
from os import unlink


def modelify(inputFile, outputFile, tagKey, tagValue):
    """ Add the <Model> entry for each group in the file """
    
    f = open(inputFile)
    f2 = open(outputFile, "w")
    
    for line in f:
        f2.write(line)
        if "row" in line:
            f2.write("  <Model> { 1 }\n")
    f.close()
    f2.close()
    

def tagify(inputFile, outputFile, tagKey, tagValue):
    """ Add the given tag to the given group. Uses the EGG API """
    
    data = EggData()
    data.read(Filename.fromOsSpecific(inputFile))
    # read out useless stuff
    child = data.getFirstChild()
    child = data.getNextChild()
    
    while child is not None:
        child = data.getNextChild()
        if type(child) is EggGroup:
            child.setTag(tagKey, tagValue)

    data.writeEgg(Filename.fromOsSpecific(outputFile))
    
            
def tessellate(inputFile, outputFile, up, us):
    """ Tessellate an EggNurbsSurface using the egg-qtess tool """
    
    # first write the parameter file
    paramFile = "/tmp/curve_params"
    f = open(paramFile, "w")
    f.write("curve : %d %d" % (up, us))
    
    cmd = "egg-qtess -cs z-up -f %s -o %s %s" % (paramFile,outputFile,inputFile)
    
    Popen(cmd.split())
    

def texturify(modelFile, outputFile, textures, tiles, startAtOffset=1):
    """ Write down textures to an egg file """
    
    if outputFile == None:
        outputFile = "%s-textured.%s" % (modelFile[:modelFile.index(".")],
                                        modelFile[modelFile.index(".")+1:])
    f = open(modelFile)
    f2 = open(outputFile, "w")
    
    # this is basically to skip the coordinate-system entry
    lines = f.readlines() 
    for i in range(startAtOffset):
         f2.write(lines[i])
    
    # write now texture references
    for texture in textures:
        f2.write("<Texture> %s {\n" % texture)
        f2.write("  %s.jpg\n" % texture)
        f2.write("  <Scalar> format { rgb }\n")
        f2.write("  <Scalar> wrap { repeat }\n")
        f2.write("}\n\n")
    
    # now write the rest of the file, adding texture refs where needed
    group = 0
    tile = 0
    for i,line in enumerate(lines[startAtOffset:]):
        f2.write(line)
        
        if "row" in line:
            group = line[line.index("-")+1:line.index("{")]
            group = int(group.rstrip())
        elif "Polygon" in line:
            tile = line[line.index("-")+1:line.index("{")]
            tile = int(tile.rstrip())
            f2.write("    <TRef> { %s }\n" % tiles[group][tile])
            

def groupify(inputFile, outputFile, polysPerGroup=5, \
             prefix="row-", polyPrefix="tile-"):
    data = EggData()
    if data.read(Filename(inputFile)):
        child = data.getFirstChild() # comment
        curve = data.getNextChild()  # curve
        vp = curve.getFirstChild() # vertex pool
        groupCount = 0
        isEof = False
        while not isEof:
            g = EggGroup("%s%d" % (prefix, groupCount))
            for i in range(polysPerGroup):
                poly = curve.getNextChild()
                if poly is None:
                    isEof = True
                    break
                poly.setName("%s%d" % (polyPrefix, i))
                g.addChild(poly)
            data.addChild(g)
            
            groupCount +=1
        data.writeEgg(Filename(outputFile))
    else:
        print "wtf, data was wrong!"
    

def holeify(inputFile, outputFile, holesIndexes, prefix="row-", 
            tilePrefix="tile-", polysPerRow=5):
    
    data = EggData()
    if data.read(Filename(inputFile)):
        child = data.getFirstChild()
        child = data.getNextChild()
        polys = 0
        while child is not None:
            child = data.getNextChild()
            if type(child) is EggGroup:
                for holeIndex in holesIndexes:
                    if holeIndex in range(polys, polys+polysPerRow):
                        idxInGroup = holeIndex - polys
                        needle = "%s%d" % (tilePrefix, idxInGroup)
                        poly = child.getFirstChild()
                        if needle in poly.getName():
                            child.removeChild(poly)
                        poly = child.getNextChild()
                        toRemove = []
                        while poly is not None:
                            if needle in poly.getName():
                                toRemove.append(poly)
                            poly = child.getNextChild()
                        for p in toRemove:
                            child.removeChild(p)
                        #poly = child.findChild()
                    
                polys += polysPerRow
    data.writeEgg(Filename(outputFile))


def enlarge(inputFile, outputFile, groupsForRow = 3, polysPerRow=5, \
            rowPrefix="row-"):
    
    data = EggData()
    if data.read(Filename(inputFile)):
        child = data.getFirstChild() # comment
        child = data.getNextChild()  # curve
        
        numOccurr = {}
        currentNum = 0
        while child is not None:
            child = data.getNextChild()
            if type(child) is EggGroup:
                groupName = child.getName()
                groupNum = groupName[groupName.index("-")+1:]
                size = child.size()
                newName = "%s%d" % (rowPrefix, currentNum)
                if size < 5:
                    currentNum += 1
                else:
                    if numOccurr.has_key(currentNum):
                        if numOccurr[currentNum] == 2:
                            currentNum +=1
                        else:
                            numOccurr[currentNum]+= 1
                            
                    else:
                        numOccurr[currentNum] = 1
                            
                child.setName(newName)
                    
                        
                    
    data.writeEgg(Filename(outputFile))
