# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

class GameMode:
    CHAMP_MODE = "champ"
    TB_MODE = "tb"
    NO_MODE = None

class TrackResult:
    tid = -1
    bestTime = ""
    attempts = 0
    bid = -1
    
    def __repr__(self):
        return "ID: %s\nBest time: %s\nAttempts: %d\nBall: %s\n" % \
        (self.tid, self.bestTime, self.attempts, self.bid)

class TrackInfo:
    ATTRIBUTES = ("gold", "silver", "bronze", "limit")
    
    tid = -1
    order = -1
    name = ""
    gold = -1
    silver = -1
    bronze = -1
    limit = -1

    def __repr__(self):
        return "ID: %s\nOrder: %s\nName: %s\nGold: %s\nSilver: %s\nBronze: \
        %s\nLimit: %s\n" % \
        (self.tid, self.order, self.name, self.gold, self.silver, self.bronze, 
         self.limit)
