# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <marco.dinacci@gmail.com>
License: BSD

This module...
"""

def Property(func):
    return property(**func())