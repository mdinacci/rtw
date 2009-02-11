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
    
    cmd = "egg-qtess -tbnauto -up %d -us %d -o %s %s" % (up, us, 
                                                         outputFile, inputFile)
    Popen(cmd.split())
    

def holeify(inputFile, outputFile, holesIndexes):
    """ 
    Remove polygons from an egg file 
    TODO: it would be nice to remove vertexes too, but it's not trivial as I 
          have to check that they're not used by other polygons
    """
    f = open(inputFile)
    f2 = open(outputFile, "w")
    
    lines = f.readlines()
    


def groupify(modelFile, outputFile=None, polysPerGroup=5, prefix="row"):
    """ Organise polysPerGroup polygons in a group """
    
    if outputFile == None:
        outputFile = "%s-grouped.%s" % (modelFile[:modelFile.index(".")],
                                        modelFile[modelFile.index(".")+1:])
    f = open(modelFile)
    f2 = open(outputFile, "w")

    inGroup = False
    firstPolygon = True
    polysCount = 0

    lines = f.readlines()
    for i,line in enumerate(lines):
        if "Polygon" in line:
            if firstPolygon:
                f2.write("}\n") # close previous group
                f2.write("<Group> %s-%d {\n" % (prefix, polysCount/polysPerGroup))
                firstPolygon = False
            elif polysCount % polysPerGroup == 0:
                f2.write("}\n")
                f2.write("<Group> %s-%d {\n" % (prefix, polysCount/polysPerGroup))
            polysCount+=1
        f2.write(line)

    f.close()
    f2.close()
