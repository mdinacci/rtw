# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from pandac.PandaModules import loadPrcFileData 
loadPrcFileData("", "show-frame-rate-meter t")
loadPrcFileData("", "want-tk #t")
loadPrcFileData("", "want-pstats 1")
loadPrcFileData("", "pstats-tasks 1")

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from mdlib.panda.sheet import Sheet
import sys

base.oobe()

do = DirectObject()
do.accept("escape", sys.exit)
do.accept("w", lambda : base.wireframeOn())

vKnot = uKnot = [0,0,0,0,1,1,1,1]

surface = Sheet("flat")
verts = [{'node':None, 'point': (3, 0, 0), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (6, 0, 0), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (9, 0, 0), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (12, 0, 0), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (3, 3, 0), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (6, 3, 0), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (9, 3, 0), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (12, 3, 0), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (3, 6, 0), 'color' : (0,0,1,0)} ,
         {'node':None, 'point': (6, 6, 0), 'color' : (0,0,1,0)} ,
         {'node':None, 'point': (9, 6, 0), 'color' : (0,0,1,0)} ,
         {'node':None, 'point': (12, 6, 0), 'color' : (0,0,1,0)} ,
         {'node':None, 'point': (3, 10, 0), 'color' : (0,1,1,0)} ,
         {'node':None, 'point': (6, 10, 0), 'color' : (0,1,1,0)} ,
         {'node':None, 'point': (9, 10, 0), 'color' : (0,1,1,0)} ,
         {'node':None, 'point': (12, 10, 0), 'color' : (0,1,1,0)}
         ]
#surface.setup(4,4,4, verts, uKnot, vKnot)
#surface.reparentTo(render)

surface2 = Sheet("curve")
verts = [
         {'node':None, 'point': (-7.5, -8., 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7.5, -8, 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-9.8, -2.7, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-5.3, -7.2, -3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (5.3, -7.2, -3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (9.8, -2.7, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-11., 4.0, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-6., -1.8, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (6., -1.8, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (11, 4.0, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         ]

surface2.setup(4,4,4, verts, uKnot, vKnot)
surface2.sheetNode.setNumUSubdiv(6)
surface2.sheetNode.setNumVSubdiv(6)
surface2.reparentTo(render)

surface2.flattenStrong()

render.analyze() 

run()