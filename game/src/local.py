# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import ConfigVariableString 

d = {}
lang = ConfigVariableString("lang").getValue()
f = open("../res/i18n/%s.txt" % lang)
for line in f:
    k,v = line[:-1].split("=")
    d[k] = unicode(v)


__all__= ["_t"]


def _t(key):
    global d
    return d[key]
