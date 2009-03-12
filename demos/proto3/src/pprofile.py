# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

__all__ = ["PlayerProfile"]

# logging
from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("editor", INFO)

import os


def gv(line):
    # take the string at the right of "=" and strip off the newline
    return line.split("=")[1][:-1]


class Track:
    tid = -1
    completed = 0
    bestTime = ""
    attempts = 0
    ballID = 0
    
    def __repr__(self):
        return "ID: %s\tCompleted: %d\tBest time: %s\tAttempts: %d\tBall: %d\n" % \
        (self.tid, self.completed, self.bestTime, self.attempts, self.ballID)


class PlayerProfile(object):
    def __init__(self):
        self.name = "player"
        self.tracks = {"champ": [], "tb": []}

    
def find():
    profiles = []
    root_dir = "../res"
    for f in os.listdir(root_dir):
        if f.endswith(".profile"):
            path = os.path.join(root_dir, f)
            profile = load(path)
            profiles.append(profile)
    
    logger.debug("Found %d profiles in %s" % (len(profiles), root_dir))
    
    return profiles


def rename(oldProfile, newProfile):
    old = "../res/%s.profile" % oldProfile
    new = "../res/%s.profile" % newProfile
    logger.info("Renaming profile %s to %s" % (old, new))
    
    f = open(old)
    f2 = open(new, "w")
    
    for line in f:
        if "name" in line:
            f2.write("name=%s\n" % newProfile)
        else:
            f2.write(line)
    
    f.close()
    f2.close()
    os.unlink(old)


def delete(name):   
    # TODO don't delete it from disk, just rename it to ".deleted" 
    f = "../res/%s.profile" % name
    newName = "../res/%s.profile.deleted" % name
    if os.path.exists(f):
        os.rename(f, newName)
        logger.info("Deleted profile %s", name)


def load(filename):
    logger.info("Loading profile from %s", filename)
    
    f = open(filename)
    
    pp = PlayerProfile()
    
    mode = ""
    currentTrack = None
    for line in f:
        if "name" in line:
            pp.name = gv(line)
        elif "champ_mode" in line:
            mode = "champ"
        elif "tb_mode" in line:
            pp.tracks[mode].append(currentTrack)
            currentTrack = None
            mode = "tb"
        elif "tid" in line:
            if currentTrack is not None:
                pp.tracks[mode].append(currentTrack)
            currentTrack = Track()
            currentTrack.tid = gv(line)
        elif "completed" in line:
            currentTrack.completed = int(gv(line))
        elif "best_time" in line:
            currentTrack.bestTime = gv(line)
        elif "attempts" in line:
            currentTrack.attempts = int(gv(line))
        elif "ball" in line:
            ballID.attempts = int(gv(line))
    
    pp.tracks[mode].append(currentTrack)
    
    return pp

    
def save(profile, filename):
    logger.info("Saving profile to %s", filename)
    
    def writeTrack(f, track):
        f.write("tid=%s\n" % track.tid)
        f.write("completed=%d\n" % track.completed)
        f.write("best_time=%s\n" % track.bestTime)
        f.write("attempts=%d\n" % track.attempts)
        f.write("ballID=%d\n" % track.ballID)
    
    f = open(filename, "w")
    
    f.write("name=%s\n" % profile.name)
    f.write("champ_mode\n")
    for track in profile.tracks["champ"]:
        writeTrack(f, track)
    f.write("tb_mode\n")
    for track in profile.tracks["tb"]:
        writeTrack(f, track)
                
if __name__ == '__main__':
    
    pass
    
    
    