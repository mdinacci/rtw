# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import EggData, EggGroup, Filename
from subprocess import Popen

def tagify(inputFile, group, tagKey, tagValue):
    """ Add the given tag to the given group. Uses the EGG API """
    
    def getGroup(data, group):
        for child in data.getChildren():
            if child.getClassType().getName() == "EggGroup" \
                and child.getName() == group:
                return child
            groupNode = getGroup(child.getChildren(), group)
            if groupNode is not None:
                return groupNode
    
    data = EggData()
    data.read(Filename.fromOsSpecific(inputFile))
    
    group = getGroup(data, group)
    if group is not None:
        group.setTag(tagKey, tagValue)
            

def tessellate(inputFile, outputFile, up, us):
    """ Tessellate an EggNurbsSurface using the egg-qtess tool """
    
    # first write the parameter file
    paramFile = "/tmp/curve_params"
    f = open(paramFile, "w")
    f.write("curve : %d %d" % (up, us))
    
    cmd = "egg-qtess -tbnauto -cs z-up -f %s -o %s %s" % (paramFile,outputFile,inputFile)
    
    Popen(cmd.split())
    

def holeify(inputFile, outputFile, holesIndexes, prefix="row-"):
    """ 
    Remove polygons from an egg file 
    TODO: it would be nice to remove vertexes too, but it's not trivial as I 
          have to check that they're not used by other polygons
    """
    
    polysPerRow = 5
    polyLines = 4

    f = open(inputFile)
    f2 = open(outputFile, "w")
    
    skipPolygon = False
    lines = f.readlines()
    polyCount = -1
    linesToSkip = 0
    for i,line in enumerate(lines):
        if linesToSkip > 0:
            linesToSkip-=1
            continue
        
        if "Polygon" in line:
            # WRONG
            if i % 3 == 0: polyCount +=1
            if polyCount in holesIndexes:
                linesToSkip = 3
                continue
        f2.write(line)
    
    
def groupify(modelFile, outputFile=None, polysPerGroup=5, duplicationFactor=3,
             rowPrefix="row", polyPrefix="tile-"):
    """ Organise polysPerGroup polygons in a group """
    
    if outputFile == None:
        outputFile = "%s-grouped.%s" % (modelFile[:modelFile.index(".")],
                                        modelFile[modelFile.index(".")+1:])
    f = open(modelFile)
    f2 = open(outputFile, "w")

    inGroup = False
    firstPolygon = True
    polysCount = 0
    polygonIndex = 0
    lines = f.readlines()
    for i,line in enumerate(lines):
        if "Polygon" in line:
            if firstPolygon:
                f2.write("}\n") # close previous group
                f2.write("<Group> %s-%d {\n" % (rowPrefix, 
                                polysCount/(polysPerGroup*duplicationFactor)))
                f2.write("  <Model> { 1 }\n")
                #f2.write("  <Collide> { Polyset keep descend }\n")
                firstPolygon = False
            elif polysCount % polysPerGroup == 0:
                f2.write("}\n")
                f2.write("<Group> %s-%d {\n" % (rowPrefix, 
                                polysCount/(polysPerGroup*duplicationFactor)))
                #f2.write("  <Collide> { Polyset keep descend }\n")
                f2.write("  <Model> { 1 }\n")
            
            polysCount+=1
            
            line = "  <Polygon> %s%s {\n" % (polyPrefix, polygonIndex)
            if polygonIndex < polysPerGroup -1:
                polygonIndex += 1
            else:
                polygonIndex = 0
            
        f2.write(line)

    f.close()
    f2.close()
