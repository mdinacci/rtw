# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

# logging
from mdlib.log import ConsoleLogger, DEBUG, INFO
logger = ConsoleLogger("state", DEBUG)

from direct.showbase.DirectObject import DirectObject
from direct.fsm import FSM

from pandac.PandaModules import VirtualFileSystem, Filename

from mdlib.panda import config as cfg
from mdlib.panda.data import GOM

import event, entity
import pprofile as profile
from pprofile import gv, kv
from data import TrackInfo, GameMode


__all__ = ["GS"]
        

class GameSession(object):
    
    def __init__(self):
        logger.debug("Creating session")
        
        self._profile = None
        self._state = GameState()
        self._gameMode = GameMode.NO_MODE
    
        self._listener = DirectObject()
        self._listener.accept(event.GAME_MODE_SELECT, self.setGameMode)
        
    def hasValidProfile(self):    
        return self._profile is not None
        
    def setGameMode(self, gameMode):
        self._gameMode = gameMode

    def getGameMode(self):
        return self._gameMode
        
    def getTrackInfo(self, tid):
        for track in self._tracks:
            if track.tid == tid:
                return track
    
    def loadLastProfile(self):
        lastProfile = cfg.strValueForKey("last_profile")
        
        prof = None
        if profile.hasProfile(lastProfile):
            logger.info("Loading profile: %s" % lastProfile)
            prof = profile.loadByName(lastProfile)
        else:
            logger.warning("Last profile not found, maybe the user has \
                erased it")
            
        self._profile = prof
    
    def loadOriginalTrackDefinitions(self):
        f = open("../res/tracks/tracks.bin")
        tracks = []
        
        trackInfo = None
        for line in f:
            if "tid" in line:
                if trackInfo is not None:
                    tracks.append(trackInfo)
                    
                trackInfo = TrackInfo()
                trackInfo.tid = gv(line)
            else:
                key = kv(line)
                val = gv(line)
                setattr(trackInfo, key, val)
        
        tracks.append(trackInfo)
        
        f.close()
        self._tracks = tracks
    
    def getTrackDefinitions(self):
        return self._tracks
    
    
    mode = property(fget = lambda self: self._gameMode)
    state = property(fget = lambda self: self._state)
    profile = property(fget = lambda self: self._profile, 
                       fset = lambda self, prof: self.__setattr__("_profile", 
                                                                  prof))


class GameState(FSM.FSM):
    OFF = -1
    INITIALISE = "Initialise"
    PLAY =  "Play"
    PAUSE = "Pause"
    
    def __init__(self):
        FSM.FSM.__init__(self, "game-state")
    
    def enterInitialise(self):
        logger.debug("Entering Initialise state")
        
        GS.loadLastProfile()
        GS.loadOriginalTrackDefinitions()
        
        # TEMPORARY load models, will be replaced by loading only level assets
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/scene.mf"),".", VirtualFileSystem.MFReadOnly)
        
        # common stuff like cups
        vfs = VirtualFileSystem.getGlobalPtr()
        vfs.mount(Filename("../res/common.mf"),".", VirtualFileSystem.MFReadOnly)
        
        # TODO cache menu resources
        # TODO put all gui resources in a multifile ?
        GOM.getEntity(entity.gold_cup_params)
        GOM.getEntity(entity.silver_cup_params)
        GOM.getEntity(entity.bronze_cup_params)
        
        # cache balls
        GOM.getEntity(entity.photon_ball_params)
        GOM.getEntity(entity.shark_ball_params)
        GOM.getEntity(entity.avg_joe_ball_params)
        GOM.getEntity(entity.turtle_king_ball_params)
        
        # TODO load custom track definitions
    
    def exitInitialise(self):
        # invalidate cache
        pass
    
    def enterPlay(self):
        pass
    
    def exitPlay(self):
        pass


GS = GameSession()
