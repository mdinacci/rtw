# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG,INFO
logger = ConsoleLogger("editor", INFO)

from data import GameMode
from data import TrackResult

import os


def kv(line):
    return line.split("=")[0]

def gv(line):
    # take the string at the right of "=" and strip off the newline
    return line.split("=")[1][:-1]


class PlayerProfile(object):
    def __init__(self, name=None):
        self.name = name
        self.tracks = {GameMode.CHAMP_MODE: [], GameMode.TB_MODE: []}
    
    def cache(self, lines):
        self._contents = lines
    
    def getTrackResult(self, tid, mode):
        trackRes = None
        for track in self.tracks[mode]:
            if track.tid == tid:
                trackRes = track
                
        return trackRes
    
    def getBestTimeForTrackAndMode(self, tid, mode):
        for track in self.tracks[mode]:
            if track.tid == tid:
                bestTime = int(track.bestTime)
        
        return bestTime
    
    def getTracksForMode(self, mode):
        return self.tracks[mode]
    
    def update(self, result, mode):
        tid = result.tid
        
        oldResult = self.getTrackResult(tid, mode)
        needsUpdate = False
        if oldResult is None:
            result.attempts = 1
        else:
            result.attempts = oldResult.attempts + 1
        if oldResult is not None:
            # always write the best time in the file
            if result.bestTime < oldResult.bestTime:
                oldResult.bestTime = result.bestTime
        
        save(self, "../res/%s.profile" % self.name)
    

def hasProfile(profile):
    result = False
    root_dir = "../res"
    for f in os.listdir(root_dir):
        if f.endswith(".profile"):
            name = f[:f.index(".")]
            result = (name == profile)
            if result: break
    
    logger.debug("Profile %s exists: %s " % (profile, result))
    
    return result
    
    
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


def loadByName(name):
    return load("../res/%s.profile" % name)


def load(filename):
    logger.info("Loading profile from %s", filename)
    
    f = open(filename)
    lines = f.readlines()
    
    pp = PlayerProfile()
    
    mode = ""
    currentTrack = None
    for line in lines:
        if "name" in line:
            pp.name = gv(line)
        elif "champ_mode" in line:
            mode = GameMode.CHAMP_MODE
        elif "tb_mode" in line:
            if currentTrack is not None:
                pp.tracks[mode].append(currentTrack)
            currentTrack = None
            mode = GameMode.TB_MODE
        elif "tid" in line:
            if currentTrack is not None:
                pp.tracks[mode].append(currentTrack)
            currentTrack = TrackResult()
            currentTrack.tid = gv(line)
        elif "best_time" in line:
            currentTrack.bestTime = int(gv(line))
        elif "attempts" in line:
            currentTrack.attempts = int(gv(line))
        elif "bid" in line:
            currentTrack.bid = gv(line)
    
    if currentTrack is not None:
        pp.tracks[mode].append(currentTrack)
    pp.cache(lines)
    
    return pp


def save(profile, filename):
    logger.info("Saving profile to %s", filename)
    
    def writeTrack(f, track):
        f.write("tid=%s\n" % track.tid)
        f.write("best_time=%s\n" % track.bestTime)
        f.write("attempts=%d\n" % track.attempts)
        f.write("bid=%s\n" % track.bid)
    
    f = open(filename, "w")
    
    f.write("name=%s\n" % profile.name)
    f.write("champ_mode\n")
    for track in profile.tracks[GameMode.CHAMP_MODE]:
        writeTrack(f, track)
    f.write("tb_mode\n")
    for track in profile.tracks[GameMode.TB_MODE]:
        writeTrack(f, track)
                
    