# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from copy import deepcopy as dc


def transpose2DMatrix(m):
    """ Transpose a rectangular two-dimensional matrix """
    return [[m[y][x] for y in range(len(m))]for x in range(len(m[0]))]

def rotateMatrixClockwise(m):
    """ Naively rotate a NxN matrix "left" """
    l = len(m[0])-1
    m2 = dc(m)
    for i,row in enumerate(m):
        for j,col in enumerate(row):
            m2[l-j][i] = m[i][j]
    return m2

def rotateMatrixAntiClockwise(m):
    """ Naively rotate a NxN matrix "right" """
    l = len(m[0])-1
    m2 = dc(m)
    for i,row in enumerate(m):
        for j,col in enumerate(row):
            m2[j][l-i] = m[i][j]
            #if m2[j][l-i] is not None:
            #    m2[j][l-i].x = i
            #    m2[j][l-i].y = j
    return m2