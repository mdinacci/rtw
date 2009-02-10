# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from subprocess import Popen


def tessellate(inputFile, outputFile):
    """ Tessellate an EggNurbsSurface using the egg-qtess tool """
    
    cmd = "egg-qtess -tbnauto -up 5 -o %s %s" % (outputFile, inputFile)
    Popen(cmd.split())

def groupify(modelFile, outputFile=None, polysPerGroup=5):
    """ Organise polysPerGroup polygons in a group """
    
    if outputFile == None:
        outputFile = "%s-grouped.%s" % (modelFile[:modelFile.index(".")],
                                        modelFile[modelFile.index(".")+1:])
    f = open(modelFile)
    f2 = open(outputFile, "w")

    inGroup = False
    firstPolygon = True
    polysCount = 1

    lines = f.readlines()
    for i,line in enumerate(lines):
        if "Polygon" in line:
            if firstPolygon:
                f2.write("}\n") # close previous group
                f2.write("<Group> segment-%d {\n" % (polysCount/polysPerGroup))
                firstPolygon = False
            if polysCount % polysPerGroup == 0:
                f2.write("}\n")
                f2.write("<Group> segment-%d {\n" % (polysCount/polysPerGroup))
            polysCount+=1
        f2.write(line)

    f.close()
    f2.close()
