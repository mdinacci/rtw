# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

def tenthsToStrTime(time):
    tens = time % 10
    seconds = (time / 10) % 60
    minutes = (time / 10) / 60
    if tens == 0:
        tens = "0"
    if seconds == 0:
        seconds = "0"
        
    return "%d:%s.%s" % (minutes, seconds, tens)
    