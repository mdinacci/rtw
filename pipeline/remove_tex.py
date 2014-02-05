#!/usr/bin/env python
# -*- coding: utf-8-*-

	
"""
Filename: remove_trefs.py
"""

def removeTexture(input, output):
    f = open(input)
    f2 = open(output, "w")

    inTex = False

    for line in f:
        if "Texture" in line:
            inTex = True
            continue
        
        if "Group" in line and inTex:
            inTex = False

        if not inTex:
            f2.write(line)
    

def removeTRefs(input, output):
    f = open(input)
    f2 = open(output, "w")

    for line in f:
        if "TRef" in line:
            continue

        f2.write(line)


if __name__ == '__main__':
    import sys
    input = sys.argv[1]
    output = sys.argv[2]
    temp = "/tmp/tex.tmp"

    print "Removing texture references from ", input

    removeTRefs(input,temp)

    print "Saving to ", temp

    print "Removing texture declarations from ", temp

    removeTexture(temp, output)

    print "Saving to ", output
    

