# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import ConfigVariableString as cs

from pandac.PandaModules import loadPrcFile

import os

__all__ = ["loadFile", "valueForKey", "setIntValueForKey", "setStrValueForKey"]


def _store(fileName, options):
    oldFile = "%s.bak" % fileName
    os.rename(fileName, oldFile)
    
    f = open(oldFile, "r")
    f2 = open(fileName, "w")
    skip = False
    for line in f:
        for key, value in options.items():
            if line.startswith(key):
                f2.write("%s %s\n" % (key, value))
                skip = True
                continue
        if not skip:
            f2.write(line)
        else:
            skip = False
        
    f.close()
    f2.close()
    os.remove(oldFile)
                

def _set(options):
    for key,value in options.items():
        cs(key).setValue(value)
          
                
def loadFile(filename):
    loadPrcFile(filename)


def strValueForKey(key):
    return cs(key).getValue()


def intValueForKey(key):
    return int(cs(key).getValue())


def boolValueForKey(key):
    return bool(int(cs(key).getValue()))


def setStrValueForKey(key, value, persist=True):
    _set({key:value})
    if persist:
        # TODO read this value from Config.prc
        _store("../res/options.prc", {key:value})


def setMultipleStrValuesForKey(options):
    _set(options)
    _store("../res/options.prc", options)


def setIntValueForKey(key, value, persist=True):
    ci(key).setValue(key, value)
    if persist:
        _store("../res/options.prc", {key:value})
