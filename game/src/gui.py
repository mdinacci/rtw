# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009
"""

from mdlib.panda import config as cfg
from mdlib.panda.input import InputManager, InputWatcher
from mdlib.panda.data import GOM
from mdlib.panda.entity import photon_ball_params, shark_ball_params, \
        avg_joe_ball_params, turtle_king_ball_params 

from direct.gui.DirectGui import *
from direct.gui.OnscreenImage import OnscreenImage

from pandac.PandaModules import TextNode, Point3, Vec4 
from pandac.PandaModules import TransparencyAttrib, Material
      
from local import *
import event, utils, entity
import pprofile as profile
from data import GameMode
from state import GS


def getOKCancelButtons(okCb, backCb):
    maps = loader.loadModel('gui/options_menu.egg')
    okButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=okCb, relief=None, pos = (0.4,0,-.15),
                     rolloverSound=None, clickSound=None,text=_t("ok"))
    
    backButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=backCb, relief=None, pos = (0.7,0,-.15),
                     rolloverSound=None, clickSound=None,text=_t("back"))
    
    return (okButton, backButton)
           
           
class YesNoDialog(DirectDialog):
    def __init__(self, parent = None, **kw):
        # Inherits from DirectFrame
        optiondefs = (
            # Define type of DirectGuiWidget
            ('buttonTextList',  [_t("yes"), _t("no")],  DGG.INITOPT),
            ('buttonValueList', [DGG.DIALOG_YES, DGG.DIALOG_NO], DGG.INITOPT),
            )
        # Merge keyword options with default options
        self.defineoptions(kw, optiondefs)
        DirectDialog.__init__(self, parent)
        self.initialiseoptions(YesNoDialog)
        

class TrackList(DirectFrame):
    
    TRACKS_PER_PAGE = 8
    
    def __init__(self, trackList, buttonCallback):
        DirectFrame.__init__(self)
        
        self._cb = buttonCallback
        
        self._trackList = trackList
        self._numPages = len(trackList) / self.TRACKS_PER_PAGE
        self._currentPage = 0
        self._page = None
        
        self._pageLabel = DirectLabel(text="/", scale=.08, pos=(-.8,0,-.7),
                                      relief=None)
        self._pageLabel.reparentTo(self)
        
        self._turnPage()
    
    def _createPage(self, tracks):
        zIdx = 0
        
        buttons = DirectFrame()
        
        maps = loader.loadModel('gui/options_menu.egg')
        for track in tracks:
            trackButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._cb, relief=None, pos = (-1.1,0,.6 + zIdx),
                     rolloverSound=None, clickSound=None,extraArgs = [track],
                     text_align=TextNode.ALeft, text="%s" % track.name)
            trackButton.reparentTo(buttons)
            zIdx -= .15
            
        return buttons
            
    def previousPage(self):
        if self._currentPage > 0:
            self._currentPage -=1
            self._turnPage()
            
    def nextPage(self):
        if self._currentPage < self._numPages-1:
            self._currentPage +=1
            self._turnPage()
   
    def _turnPage(self):
        start = self._currentPage * self.TRACKS_PER_PAGE
        end = start + self.TRACKS_PER_PAGE

        if self._page is not None:
            self._page.destroy()
        self._page = self._createPage(self._trackList[start:end])
        self._page.reparentTo(self)
        
        self._pageLabel["text"] = "%d/%d" % (self._currentPage+1,self._numPages)
            
        
class Screen(object):
    
    name = "default"
    
    def __init__(self):
        self.frame = DirectFrame()
    
    def destroy(self):
        self.frame.destroy()
        
    def hide(self):
        self.frame.hide()
        
    def show(self):
        self.frame.show()


class MainScreen(Screen):
    
    name = "main"
    
    def __init__(self, screenMgr):
        super(MainScreen, self).__init__()
        
        self.screenMgr = screenMgr
        
        maps = loader.loadModel('gui/options_menu.egg')
        champButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.8,0,.7),
                         rolloverSound=None, clickSound=None,
                         command=self.champModePressed, text="Champ Mode")
        battleButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.8,0,.3),
                         rolloverSound=None, clickSound=None,
                         command=self.timeModePressed, text="Time Battle")
        trackDesButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.8,0,-.1),
                         rolloverSound=None, clickSound=None,
                         command=self.timeModePressed, text="Track Designer")
        optionsButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (-.95,0,-.8),
                         rolloverSound=None, clickSound=None,
                         command=self.optionPressed,text="Options")
        profileButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (0,0,-.8),
                         rolloverSound=None, clickSound=None,
                         command=self.profilePressed, text="Profile")
        exitButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (0.95,0,-.8),
                         rolloverSound=None, clickSound=None,
                         command=self.exitPressed, text="Exit")
        
        champButton.reparentTo(self.frame)
        battleButton.reparentTo(self.frame)
        trackDesButton.reparentTo(self.frame)
        optionsButton.reparentTo(self.frame)
        profileButton.reparentTo(self.frame)
        exitButton.reparentTo(self.frame)
        
        
    def exitPressed(self):
        messenger.send(event.GAME_EXIT_REQUEST)
        
    def optionPressed(self):
        self.screenMgr.displayScreen("options")
    
    def profilePressed(self):
        self.screenMgr.displayScreen("profile")
    
    def champModePressed(self):
        messenger.send(event.GAME_MODE_SELECT, [GameMode.CHAMP_MODE])
        
        if GS.hasValidProfile():
            self.screenMgr.displayScreen("track-selection")
        else:
            self.screenMgr.setNextScreen("track-selection")
            self.screenMgr.displayScreen("new-profile")
            
        """
        lastProfile = cfg.strValueForKey("last_profile")
        if profile.hasProfile(lastProfile):
            self.screenMgr.displayScreen("track-selection")
        else:
            self.screenMgr.setNextScreen("track-selection")
            self.screenMgr.displayScreen("new-profile")
        """
        
    def timeModePressed(self):
        messenger.send(event.GAME_MODE_SELECT, [GameMode.TB_MODE])
        self.screenMgr.displayScreen("ball-selection")


class TrackResultFrame(DirectFrame):
    
    def __init__(self, trackResult, screenMgr):
        DirectFrame.__init__(self)
        
        self.screenMgr = screenMgr
        
        if trackResult.trophy is not None:
            cup = GOM.getEntity(trackResult.trophy)
            cup.nodepath.reparentTo(render)
            cup.nodepath.hprInterval(10, Point3(360,0,0)).loop()
            from pandac.PandaModules import AntialiasAttrib
            cup.nodepath.setAntialias(AntialiasAttrib.MMultisample)
            
            from pandac.PandaModules import *
            lAttrib = LightAttrib.makeAllOff()
            ambientLight = AmbientLight( "ambientLight" )
            ambientLight.setColor( Vec4(.4, .4, .35, 1) )
            lAttrib = lAttrib.addLight( ambientLight )
            directionalLight = DirectionalLight( "directionalLight" )
            directionalLight.setDirection( Vec3( 0, 8, -2.5 ) )
            directionalLight.setColor( Vec4( 0.9, 0.8, 0.9, 1 ) )
            lAttrib = lAttrib.addLight( directionalLight )
            cup.nodepath.attachNewNode( directionalLight.upcastToPandaNode() )
            cup.nodepath.attachNewNode( ambientLight.upcastToPandaNode() )
            cup.nodepath.node().setAttrib( lAttrib )
        else:
            pass
        
        bestTimeLabel = DirectLabel(text="Best time", scale=.1, 
                                 pos=(0.2,0,-0.1),
                                 text_align=TextNode.ALeft, relief=None)
        ballLabel = DirectLabel(text="Ball", scale=.1, 
                                 pos=(0.2,0,-0.25),
                                 text_align=TextNode.ALeft, relief=None)
        
        time = utils.tenthsToStrTime(int(trackResult.bestTime))
        resultTime = DirectLabel(text=time, scale=.1, 
                                 pos=(0.7,0,-0.1),
                                 text_align=TextNode.ALeft, relief=None)
        resultBall = DirectLabel(text=str(trackResult.bid), scale=.1, 
                                 pos=(0.7,0,-0.25),
                                 text_align=TextNode.ALeft, relief=None)
        
        maps = loader.loadModel('gui/options_menu.egg')
        selectButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._selectPressed, extraArgs=[trackResult.tid],
                     relief=None,pos = (0.45,0,-.4),rolloverSound=None, 
                     clickSound=None,text="Select")
        
        selectButton.reparentTo(self)
        bestTimeLabel.reparentTo(self)
        ballLabel.reparentTo(self)
        resultTime.reparentTo(self)
        resultBall.reparentTo(self)
        
    def _selectPressed(self, track):
        messenger.send(event.TRACK_SELECTED, [track])
        self.screenMgr.displayScreen("ball-selection")
    
    
class TrackSelectionScreen(Screen):
    
    name = "track-selection"
    
    def __init__(self, screenMgr, tracks):
        super(TrackSelectionScreen, self).__init__()
        
        self.screenMgr = screenMgr
        
        maps = loader.loadModel('gui/options_menu.egg')
        
        trackLabel = DirectLabel(text="Choose track", scale=.1, 
                                 pos=(-1.0,0,.8),
                                 text_align=TextNode.ALeft, relief=None)
        
        backButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._backPressed, relief=None, pos = (0.9,0,-.9),
                     rolloverSound=None, clickSound=None,text=_t("back"))
        
        self._trackList = TrackList(tracks, self._trackPressed)
        
        prevButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._trackList.previousPage, relief=None, 
                     pos = (-1.1,0,-.7), rolloverSound=None, clickSound=None,
                     text="<", text_align=TextNode.ALeft)
        
        nextButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._trackList.nextPage, relief=None, 
                     pos = (-0.5,0,-.7), rolloverSound=None, clickSound=None,
                     text=">", text_align=TextNode.ALeft)
        
        trackLabel.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        
        self._trackList.reparentTo(self.frame)
        prevButton.reparentTo(self.frame)
        nextButton.reparentTo(self.frame)
        
        self._trackResult = None
        
    def _trackPressed(self, track):
        result = GS.profile.getTrackResult(track.tid, GS.mode)
        info = GS.getTrackInfo(track.tid)
        result.trophy = None
        if result.bestTime <= info.bronze:
            result.trophy = entity.bronze_cup_params
        if result.bestTime <= info.silver:
            result.trophy = entity.silver_cup_params
        if result.bestTime <= info.gold:
            result.trophy = entity.gold_cup_params
        
        self._showTrackResult(result)
        
    def _showTrackResult(self, result):
        if self._trackResult is not None:
            self._trackResult.destroy()
        self._trackResult = TrackResultFrame(result, self.screenMgr)
        self._trackResult.reparentTo(self.frame)
    
    def _backPressed(self):
        self.screenMgr.displayPreviousScreen()
        

class RenameProfileMenuScreen(Screen):
    
    name = "rename-profile"
    
    def __init__(self, screenMgr, oldProfileName):
        super(RenameProfileMenuScreen, self).__init__()
        
        okButton, backButton = getOKCancelButtons(self._renameProfile, \
                           self._backPressed)
        
        self.screenMgr = screenMgr
        self._oldProfileName = oldProfileName
        
        
        self.nameEntry = DirectEntry(text=self._oldProfileName, initialText="",
                             pos = (-0.7,0,0.4), cursorKeys=1,
                             command=self._renameProfile, numLines = 1,
                             focusInCommand=self._eraseText, width=30,scale=.05,
                             rolloverSound=None, clickSound=None)
        
        self.warning = OnscreenText(text = _t("warn_profile_exists"), 
        pos = (-0.1,-0.4), scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        
        self.warning.hide()

        self.nameEntry.reparentTo(self.frame)
        okButton.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        
    def _eraseText(self):
        self.warning.hide()
        self.nameEntry["text"] = ""
    
    def _renameProfile(self, text=None):
        newProfile = ""
        if text:
            newProfile = text
        else:
            newProfile = self.nameEntry.get()
        
        newProfile = newProfile.strip()
        
        if newProfile != "" and newProfile != _t("new_profile"):
            # search for duplicate names
            profileExists = False
            profiles = profile.find()
            for prof in profiles:
                if newProfile == prof.name:
                    profileExists = True
                    self.warning.show()
                    break
                
            if not profileExists:
                profile.rename(self._oldProfileName, newProfile)
                
                lastProfile = cfg.strValueForKey("last_profile")
                if self._oldProfileName == lastProfile:
                    cfg.setStrValueForKey("last_profile", newProfile)
                
                self.screenMgr.displayScreen("main")
            else:
                self.warning.show()


    def _backPressed(self):
        self.screenMgr.displayScreen("main")
        

class NewProfileMenuScreen(Screen):
    
    name = "new-profile"
    
    def __init__(self, screenMgr):
        super(NewProfileMenuScreen, self).__init__()
        
        okButton, backButton = getOKCancelButtons(self._createProfile, \
                           self._backPressed)
        
        self.screenMgr = screenMgr
        
        self.nameEntry = DirectEntry(text=_t("new_profile"), initialText="",
                             pos = (-0.7,0,0.4), cursorKeys=1,
                             command=self._createProfile, numLines = 1,
                             focusInCommand=self._eraseText, width=30,scale=.05,
                             rolloverSound=None, clickSound=None)
        
        self.warning = OnscreenText(text = _t("warn_profile_exists"), 
        pos = (-0.1,-0.4), scale = 0.07,fg=(1,0.5,0.5,1),align=TextNode.ACenter)
        
        self.warning.hide()

        self.nameEntry.reparentTo(self.frame)
        okButton.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        
    def _eraseText(self):
        self.warning.hide()
        self.nameEntry["text"] = ""
                
    def _createProfile(self, text=None):
        pp = profile.PlayerProfile()

        if text:
            pp.name = text
        else:
            pp.name = self.nameEntry.get()
        
        pp.name = pp.name.strip()
        
        if pp.name != "" and pp.name != _t("new_profile"):
            # search for duplicate names
            profileExists = False
            profiles = profile.find()
            for prof in profiles:
                if pp.name == prof.name:
                    profileExists = True
                    self.warning.show()
                    break
                
            if not profileExists:
                self.warning.hide() # in case it was shown
                profile.save(pp, "../res/%s.profile" % pp.name)
                cfg.setStrValueForKey("last_profile", pp.name)
                
                # TODO select profile (visually)
                GS.profile = pp
                
                if self.screenMgr.hasNextScreen():
                    self.screenMgr.displayNextScreen()
                else:
                    self.screenMgr.displayPreviousScreen()
                    
            else:
                self.warning.show()


    def _backPressed(self):
        self.screenMgr.displayScreen("main")
        
        
class ProfileMenuScreen(Screen):  
    
    name = "profile"
    
    def __init__(self, screenMgr):
        super(ProfileMenuScreen, self).__init__()
        
        self.screenMgr = screenMgr
        
        profiles = profile.find()
        
        maps = loader.loadModel('gui/options_menu.egg')
        
        text = _t("new")
        if len(profiles) > 0:
            text = profiles[0].name
        self.pro1Button = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,.6),
                         rolloverSound=None, clickSound=None,
                         command=self._profileSelected, text=text)
        self.pro1Button["extraArgs"] = [self.pro1Button]
        if text != _t("new"):
            self._showTools(text, .55)
        
        if len(profiles) > 1:
            text = profiles[1].name
        else:
            text = _t("new")
        self.pro2Button = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,.2),
                         rolloverSound=None, clickSound=None,
                         command=self._profileSelected, text=text)
        self.pro2Button["extraArgs"] = [self.pro2Button]
        if text != _t("new"):
            self._showTools(text, .15)
            
        if len(profiles) > 2:
            text = profiles[2].name
        else:
            text = _t("new")
        self.pro3Button = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0, -.2),
                         rolloverSound=None, clickSound=None,
                         command=self._profileSelected, text=text)
        self.pro3Button["extraArgs"] = [self.pro3Button]
        if text != _t("new"):
            self._showTools(text, -.15)
        
        backButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (0.9,0,-.9),
                         rolloverSound=None, clickSound=None,
                         command=self._backPressed, text=_t("back"))
        
        self.pro1Button.reparentTo(self.frame)
        self.pro2Button.reparentTo(self.frame)
        self.pro3Button.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        
        
    def _showTools(self, text, z):
        maps = loader.loadModel('gui/options_menu.egg')
        renameButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.15,borderWidth=(0,0),
                     relief=None, pos=(0.4,0,z),
                     rolloverSound=None, clickSound=None,
                     command=self._renameProfile, text="r")
        renameButton["extraArgs"] = [text]
        delButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.15,borderWidth=(0,0),
                     relief=None, pos=(0.6, 0, z),
                     rolloverSound=None, clickSound=None,
                     command=self._deleteProfile, text="x")
        delButton["extraArgs"] = [text]
        
        renameButton.reparentTo(self.frame)
        delButton.reparentTo(self.frame)

    def _renameProfile(self, profileName):
        self.screenMgr.displayScreen("rename-profile", profileName)
    
    def _deleteProfile(self, profileName):
        profile.delete(profileName)
        
        if profileName == GS.profile.name:
            GS.profile = None 
        
        self.screenMgr.displayScreen("profile")
    
    def _backPressed(self):
        self.screenMgr.displayScreen("main")
    
    def _profileSelected(self, button):
        if button["text"] == _t("new"):
            self.screenMgr.displayScreen("new-profile")
        else:
            # select profile
            pass
    

class PauseMenuScreen(Screen):  
    
    name = "pause"
    
    def __init__(self, screenMgr):
        super(PauseMenuScreen, self).__init__()
        
        self.screenMgr = screenMgr
        
        maps = loader.loadModel('gui/options_menu.egg')
        continueButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,.4),
                         rolloverSound=None, clickSound=None,
                         command=self._continuePressed, text=_t("continue"))
        restartButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,.2),
                         rolloverSound=None, clickSound=None,
                         command=self._restartPressed, text=_t("restart_track"))
        mainMenuButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,.0),
                         rolloverSound=None, clickSound=None,
                         command=self._mainMenuPressed, text=_t("back_to_main_menu"))
        exitButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos=(0, 0,-.2),
                         rolloverSound=None, clickSound=None,
                         command=self._exitPressed, text=_t("quit_game"))
        
        continueButton.reparentTo(self.frame)
        restartButton.reparentTo(self.frame)
        mainMenuButton.reparentTo(self.frame)
        exitButton.reparentTo(self.frame)
        
        self.frame["frameColor"] = (0,1,0,.6)
        self.frame["relief"] = DGG.FLAT 
        self.frame["frameSize"] = (-0.6, .6, .6, -.4)
        
        
    def _continuePressed(self):
        self.screenMgr.destroyCurrent()
        messenger.send(event.UNPAUSE_GAME)
        
    def _restartPressed(self):
        self.screenMgr.destroyCurrent()
        messenger.send(event.RESTART_TRACK)
        
    def _mainMenuPressed(self):
        messenger.send(event.QUIT_TRACK)
        self.screenMgr.displayScreen("main")
        
    def _exitPressed(self):
        self.screenMgr.displayScreen("exit")
        
        
class OptionsMenuScreen(Screen):
    
    name = "options"
    
    def __init__(self, screenMgr):
        super(OptionsMenuScreen, self).__init__()
        
        self.screenMgr = screenMgr
        
        maps = loader.loadModel('gui/options_menu.egg')
        videoButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos = (-.8,0,.8),
                         rolloverSound=None, clickSound=None,
                         command=self._videoPressed, text="Video")
        audioButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos = (-0.3,0,.8),
                         rolloverSound=None, clickSound=None,
                         command=self._audioPressed, text="Audio")
        
        controlsButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos = (0.2,0,.8),
                         rolloverSound=None, clickSound=None,
                         command=self._controlsPressed, text="Controls")
        
        netButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.15,borderWidth=(0,0),
                         relief=None, pos = (0.7,0,.8),
                         rolloverSound=None, clickSound=None,
                         command=self._networkPressed, text="Network")
        
        resetButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (-0.9,0,-.9),
                         rolloverSound=None, clickSound=None,
                         command=self._resetPressed, text="Reset")
        
        backButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (0.9,0,-.9),
                         rolloverSound=None, clickSound=None,
                         command=self._backPressed, text=_t("back"))
        
        videoButton.reparentTo(self.frame)
        audioButton.reparentTo(self.frame)
        controlsButton.reparentTo(self.frame)
        netButton.reparentTo(self.frame)
        resetButton.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        
        self.currentOptions = None
        
        # by default show video options
        self._videoPressed()
        
        
    def _newOptionsPage(self, optionsPage):
        if self.currentOptions is not None:
            self.currentOptions.destroy()
            
        self.currentOptions = optionsPage
        self.currentOptions.show()
    
    def _videoPressed(self):
        self._newOptionsPage(VideoOptions())
    
    def _audioPressed(self):
        self._newOptionsPage(AudioOptions())
    
    def _controlsPressed(self):
        self._newOptionsPage(ControlsOptions())
    
    def _networkPressed(self):
        self._newOptionsPage(NetworkOptions())
    
    def _resetPressed(self):
        messenger.send(event.OPTIONS_RESET)
        # refresh
        self._newOptionsPage(self.currentOptions)
    
    def _backPressed(self):
        # TODO save configuration
        self.currentOptions.destroy()
        self.screenMgr.displayScreen("main")


class ExitRequestScreen(object):
    name = "exit"
    
    def __init__(self, screenMgr):
        self.dialog = YesNoDialog(dialogName="YesNoCancelDialog", \
                          text=_t("quit_game_question"), command=self.dialogCallback)
        
        self.screenMgr = screenMgr

    def dialogCallback(self, yes):
        if yes:
            messenger.send(event.GAME_DESTROY)
        else:
            self.screenMgr.displayPreviousScreen()
    
    def destroy(self):
        self.dialog.cleanup()


class BallSelectionScreen(Screen):

    name = "ball-selection"
    
    def __init__(self, screenMgr):
        super(BallSelectionScreen, self).__init__()
        
        self.screenMgr = screenMgr

        self._ball0 = GOM.getEntity(photon_ball_params)
        self._ball1 = GOM.getEntity(shark_ball_params)
        self._ball2 = GOM.getEntity(avg_joe_ball_params)
        self._ball3 = GOM.getEntity(turtle_king_ball_params)
        self._balls = [self._ball0, self._ball1, self._ball2, self._ball3]
        
        startPos = Point3(-.75,0,.6)
        for i, ball in enumerate(self._balls):
            ball.nodepath.reparentTo(aspect2d)
            ball.nodepath.setScale(.3)
            pos = startPos + Point3(i*.5,0,0)
            ball.nodepath.setPos(pos)
            ball.nodepath.setTransparency(TransparencyAttrib.MAlpha)
            
        self._selectedBallIdx = 0
        self._selectedBall = self._balls[0]
        
        maps = loader.loadModel('gui/options_menu.egg')
        
        leftButton = DirectButton(geom = (maps.find('**/test'),
                 maps.find('**/test'),maps.find('**/test'),
                 maps.find('**/test')),scale=.1,borderWidth=(0,0),
                 command=self._selectPreviousBall,
                 relief=None, pos = (0.9,0,-.1),
                 rolloverSound=None, clickSound=None,text="<")
        rightButton = DirectButton(geom = (maps.find('**/test'),
                 maps.find('**/test'),maps.find('**/test'),
                 maps.find('**/test')),scale=.1,borderWidth=(0,0),
                 command=self._selectNextBall, relief=None, pos = (1.0,0,-.1),
                 rolloverSound=None, clickSound=None,text=">")
        
        selectButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._selectPressed, relief=None, pos = (0.9,0,-.9),
                     rolloverSound=None, clickSound=None,text=_t("select"))
        
        backButton = DirectButton(geom = (maps.find('**/test'),
                     maps.find('**/test'),maps.find('**/test'),
                     maps.find('**/test')),scale=.1,borderWidth=(0,0),
                     command=self._backPressed, relief=None, pos = (-0.9,0,-.9),
                     rolloverSound=None, clickSound=None,text=_t("back"))
        
        selectButton.reparentTo(self.frame)
        backButton.reparentTo(self.frame)
        leftButton.reparentTo(self.frame)
        rightButton.reparentTo(self.frame)
        
        self._propsFrame = None
        
        self._selectBall()
    
    
    def _showBallProperties(self):
        ball = self._selectedBall.props
        
        if self._propsFrame is not None:
            self._propsFrame.destroy()
            
        self._propsFrame = DirectFrame()
        
        # TODO positions should be relative to text 
        self._name = DirectLabel(text="Speed", scale=.15, pos=(-1.0,0,0.05),
                                 text_align=TextNode.ALeft, relief=None)
        speed = DirectWaitBar(text = "" , value=ball.speed, scale=.3, 
                              pos=(-.4, 0, -.1),
                              barBorderWidth=(.01,.01), barRelief=DGG.RAISED)
        control = DirectWaitBar(text = "" , value=ball.control, scale=.3, 
                              pos=(-.4, 0, -.2),
                              barBorderWidth=(.01,.01), barRelief=DGG.RAISED)
        jump = DirectWaitBar(text = "" , value=ball.jump, scale=.3, 
                              pos=(-.4, 0, -.3), 
                              barBorderWidth=(.01,.01), barRelief=DGG.RAISED)
        accel = DirectWaitBar(text = "" , value=ball.acceleration, scale=.3, 
                              pos=(-.4, 0, -.4),
                              barBorderWidth=(.01,.01), barRelief=DGG.RAISED)
        
        speedLabel = DirectLabel(text="Speed", scale=.05, pos=(-1.0,0,-.12),
                                 text_align=TextNode.ALeft, relief=None)
        controlLabel = DirectLabel(text="Control", scale=.05, pos=(-1.0,0,-.22),
                                 text_align=TextNode.ALeft, relief=None)
        jumpLabel = DirectLabel(text="Jump", scale=.05, pos=(-1.0,0,-.32),
                                 text_align=TextNode.ALeft, relief=None)
        accelLabel = DirectLabel(text="Acceleration",scale=.05,pos=(-1.0,0,-.42),
                                 text_align=TextNode.ALeft, relief=None)
        
        self._name.reparentTo(self._propsFrame)
        speedLabel.reparentTo(self._propsFrame)
        controlLabel.reparentTo(self._propsFrame)
        jumpLabel.reparentTo(self._propsFrame)
        accelLabel.reparentTo(self._propsFrame)
        
        speed.reparentTo(self._propsFrame)
        control.reparentTo(self._propsFrame)
        jump.reparentTo(self._propsFrame)
        accel.reparentTo(self._propsFrame)
        
        self._propsFrame.reparentTo(self.frame)
        
    
    def _selectNextBall(self):
        if self._selectedBallIdx < len(self._balls)-1:
            self._selectedBallIdx += 1
            self._selectBall()
        
    def _selectPreviousBall(self):
        if self._selectedBallIdx > 0:
            self._selectedBallIdx -= 1
            self._selectBall()
    
    def _selectBall(self):
        for ball in self._balls:
            ball.nodepath.setSa(.4)
            ball.nodepath.setScale(.3)
            
        self._selectedBall = self._balls[self._selectedBallIdx]
        self._selectedBall.nodepath.setScale(.4)
        self._selectedBall.nodepath.setSa(1)
        
        self._showBallProperties()
        
        self._name["text"] = self._selectedBall.prettyName
    
    def _selectPressed(self):
        messenger.send(event.BALL_SELECTED, [self._selectedBall.prettyName])
        messenger.send(event.GAME_START)
        
    def _backPressed(self):
        self.screenMgr.displayScreen("main")
        
    def destroy(self):
        super(BallSelectionScreen, self).destroy()
        for ball in self._balls:
            if ball is not self._selectedBall:
                ball.nodepath.removeNode()
                del ball


class ScreenManager(object):
    def __init__(self):
        self._currentScreen = None
        self._previousScreen = None
        self._nextScreen = None
        
    def displayScreen(self, name, *params):
        if self._currentScreen is not None:
            self._previousScreen = self._currentScreen.name
        if self._previousScreen is not None:
            self.destroyCurrent()
        
        if name == "main":
            self._currentScreen = MainScreen(self)
        elif name == "exit":
            self._currentScreen = ExitRequestScreen(self)
        elif name == "options":
            self._currentScreen = OptionsMenuScreen(self)
        elif name == "profile":
            self._currentScreen = ProfileMenuScreen(self)
        elif name == "pause":
            self._currentScreen = PauseMenuScreen(self)
        elif name == "new-profile":
            self._currentScreen = NewProfileMenuScreen(self)
        elif name == "rename-profile":
            # HACK ...
            self._currentScreen = RenameProfileMenuScreen(self, params[0])
        elif name == "ball-selection":
            self._currentScreen = BallSelectionScreen(self)
        elif name == "track-selection":
            
            #tracks = GS.profile.getTracksForMode(GS.mode)
            tracks = GS.getTrackDefinitions()
            self._currentScreen = TrackSelectionScreen(self, tracks)
        
        return self._currentScreen
    
    def hasNextScreen(self):
        return self._nextScreen is not None

    def setNextScreen(self, name):
        self._nextScreen = name

    def displayNextScreen(self):
        self.displayScreen(self._nextScreen)

    def displayPreviousScreen(self):
        self.displayScreen(self._previousScreen)

    def destroyCurrent(self):
        self._currentScreen.destroy()
    

class AudioOptions(DirectFrame):
    def __init__(self):
        DirectFrame.__init__(self)
        
        self._hasChanged = False
        
        soundLabel = DirectLabel(text=unicode(_t("options_sound_on_off")), 
                                      pos=(-.7,0,.4), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        
        volumeLabel = DirectLabel(text=unicode(_t("options_sound_volume")), 
                                      pos=(-.7,0,.2), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        
        soundLabel.reparentTo(self)
        volumeLabel.reparentTo(self)
        
        self.soundCheckBox = DirectCheckButton(pos=(.7,0,.4), relief=None, scale=.1,
                   command=self.soundToggle,
                   rolloverSound=None, clickSound=None,
                   indicatorValue=cfg.intValueForKey("options_sound_on_off"))
        self.volumeSlider = DirectSlider(value=3, range=(0,5), pos = (.7,0,.2),
                                         scale=.2, pageSize=3)
        
        self.soundCheckBox.reparentTo(self)
        self.volumeSlider.reparentTo(self)
        

    def soundToggle(self, status):
        self._hasChanged = True
        messenger.send(event.TOGGLE_SOUND)
        
    def destroy(self):
        if self._hasChanged:
            cfg.setStrValueForKey("options_sound_on_off", 
                                  str(self.soundCheckBox["indicatorValue"]))
        
        DirectFrame.destroy(self)
        
            
class NetworkOptions(DirectFrame):
    def __init__(self):
        DirectFrame.__init__(self)
        
        self._hasChanged = False
        
        onlineModeLabel = DirectLabel(text=unicode(_t("options_online_mode")), 
                                      pos=(-.7,0,.4), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        onlineModeLabel.reparentTo(self)
        
        self.onlineCheckBox = DirectCheckButton(pos=(.7,0,.4), relief=None, scale=.1,
                       command=self.onlineToggle,
                       rolloverSound=None, clickSound=None,
                       indicatorValue=cfg.intValueForKey("options_online_mode"))
        self.onlineCheckBox.reparentTo(self)


    def onlineToggle(self, status):
        self._hasChanged = True
        
        if status:
            messenger.send(event.ACTIVATE_ONLINE_MODE)
        else:
            messenger.send(event.DESACTIVATE_ONLINE_MODE)
            
    def destroy(self):
        if self._hasChanged:
            cfg.setStrValueForKey("options_online_mode", 
                                  str(self.onlineCheckBox["indicatorValue"]))
        
        DirectFrame.destroy(self)


class ControlsOptions(DirectFrame, InputWatcher):
    def __init__(self):
        DirectFrame.__init__(self)
        
        self._changes = {}
        
        self._currentButton = None
        self._inputMgr = InputManager()
        self._inputMgr.addWatcher(self)

        accelerateLabel = DirectLabel(text=unicode(_t("options_accelerate")), 
                                      pos=(-.7,0,.4), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        brakeLabel = DirectLabel(text=unicode(_t("options_brake")), 
                                      pos=(-.7,0,.2), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        steerRightLabel = DirectLabel(text=unicode(_t("options_steer_right")), 
                                      pos=(-.7,0,.0), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        steerLeftLabel = DirectLabel(text=unicode(_t("options_steer_left")), 
                                      pos=(-.7,0,-.2), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        jumpLabel = DirectLabel(text=unicode(_t("options_jump")), 
                                      pos=(-.7,0,-.4), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        
        accelerateLabel.reparentTo(self)
        brakeLabel.reparentTo(self)
        steerRightLabel.reparentTo(self)
        steerLeftLabel.reparentTo(self)
        jumpLabel.reparentTo(self)
        
        maps = loader.loadModel('gui/options_menu.egg')
        self.accelerateButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,.4), text_scale=(.5,.5),
                         command=self._changeKey, 
                         text=cfg.strValueForKey("options_accelerate"),
                         pressEffect=0,rolloverSound=None, clickSound=None)
        self.accelerateButton["extraArgs"] = [self.accelerateButton, 
                                              "options_accelerate"]
        self.brakeButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,.2), text_scale=(.5,.5),
                         command=self._changeKey, 
                         text=cfg.strValueForKey("options_brake"),
                         pressEffect=0,rolloverSound=None, clickSound=None)
        self.brakeButton["extraArgs"] = [self.brakeButton, "options_brake"]
        self.steerRightButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,.0), text_scale=(.5,.5),
                         command=self._changeKey, 
                         text=cfg.strValueForKey("options_steer_right"),
                         pressEffect=0,rolloverSound=None, clickSound=None)
        self.steerRightButton["extraArgs"] = [self.steerRightButton,
                                              "options_steer_right"]
        self.steerLeftButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,-.2), text_scale=(.5,.5),
                         command=self._changeKey, 
                         text=cfg.strValueForKey("options_steer_left"),
                         pressEffect=0,rolloverSound=None, clickSound=None)
        self.steerLeftButton["extraArgs"] = [self.steerLeftButton,
                                              "options_steer_left"]
        self.jumpButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,-.4), text_scale=(.5,.5),
                         command=self._changeKey,
                         text=cfg.strValueForKey("options_jump"),  
                         pressEffect=0,rolloverSound=None, clickSound=None)
        self.jumpButton["extraArgs"] = [self.jumpButton, "options_jump"]
        
        self.accelerateButton.reparentTo(self)
        self.brakeButton.reparentTo(self)
        self.steerRightButton.reparentTo(self)
        self.steerLeftButton.reparentTo(self)
        self.jumpButton.reparentTo(self)

    def acceptUp(self, key):
        # discard mouse input
        if "mouse" in key: return
        if self._currentButton is not None:
            value = key.split("-")[0]
            self._currentButton["text"] = value
            self._currentButton = None
            self._changes[self._currentOption] = value
            
    def destroy(self):
        if len(self._changes) > 0:
            cfg.setMultipleStrValuesForKey(self._changes)
        
        DirectFrame.destroy(self)
        del self._inputMgr

    def _changeKey(self, button, option):
        self._currentButton = button
        self._currentOption = option
        button["text"] = _t("options_controls_change_key")
        

class VideoOptions(DirectFrame):

    normal_resolutions = ["800x600","1024x768", "1280x1024", 
                          "1400x1050", "1600x1200"]
    wide_resolutions = ["1280x800", "1440x900", "1680x1050", "1920x1200"]
    
    def __init__(self):
        DirectFrame.__init__(self)
        
        self._hasChanged = False
        
        fullScreenLabel = DirectLabel(text=_t("options_fullscreen"), 
                                      pos=(-.7,0,.4), text_scale=(.1,.1),
                                      text_align=TextNode.ALeft,
                                      relief=None)
        aspectLabel = DirectLabel(text=_t("options_aspect"),
                                      pos=(-.7,0,0.2), text_scale=(.1,.1), 
                                      text_align=TextNode.ALeft,
                                      relief=None) 
        resLabel = DirectLabel(text=_t("options_resolution"),
                                      pos=(-.7,0,0.0), text_scale=(.1,.1), 
                                      text_align=TextNode.ALeft,
                                      relief=None) 
        qualityLabel = DirectLabel(text=_t("options_video_quality"),
                                      pos=(-.7,0,-0.2), text_scale=(.1,.1), 
                                      text_align=TextNode.ALeft,
                                      relief=None)
        
        fullScreenLabel.reparentTo(self)
        aspectLabel.reparentTo(self)
        resLabel.reparentTo(self)
        qualityLabel.reparentTo(self)
        
        self.fsCheckBox = DirectCheckButton(pos=(.7,0,.4), relief=None, scale=.1,
                       command=self._fullScreenToggle,
                       rolloverSound=None, clickSound=None,
                       indicatorValue=int(cfg.strValueForKey("options_fullscreen")))
        
        maps = loader.loadModel('gui/options_menu.egg')
        self.aspectButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,.2),
                         rolloverSound=None, clickSound=None,
                         command=self._valueChanged, text_scale=(.5,.5),
                         text=_t(cfg.strValueForKey("options_aspect")))
        self.aspectButton["extraArgs"] = [self.aspectButton]
        
        self.resolutionButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,0),
                         rolloverSound=None, clickSound=None,
                         command=self._valueChanged, text_scale=(.5,.5),
                         text=cfg.strValueForKey("options_resolution"))
        self.resolutionButton["extraArgs"] = [self.resolutionButton]
        
        self.qualityButton = DirectButton(geom = (maps.find('**/test'),
                         maps.find('**/test'),maps.find('**/test'),
                         maps.find('**/test')),scale=.2,borderWidth=(0,0),
                         relief=None, pos = (.7,0,-.2),
                         rolloverSound=None, clickSound=None,
                         command=self._valueChanged, text_scale=(.5,.5),
                         text=_t(cfg.strValueForKey("options_video_quality")))
        self.qualityButton["extraArgs"] = [self.qualityButton]
        
        self.fsCheckBox.reparentTo(self)
        self.aspectButton.reparentTo(self)
        self.resolutionButton.reparentTo(self)
        self.qualityButton.reparentTo(self)
   
    def _fullScreenToggle(self, status):     
        self._hasChanged = True
        
    def _valueChanged(self, item):
        self._hasChanged = True
        
        if item is self.aspectButton:
            if item["text"] is _t("options_aspect_normal"):
                item["text"] = _t("options_aspect_wide")
                self.resolutionButton["text"] = self.wide_resolutions[1]
            else:
                item["text"] = _t("options_aspect_normal")
                self.resolutionButton["text"] = self.normal_resolutions[1]
        elif item is self.resolutionButton:
            idx = 0
            text = ""
            if self.aspectButton["text"] is _t("options_aspect_normal"):
                idx = self.normal_resolutions.index(item["text"])
                if idx == len(self.normal_resolutions) -1:
                    idx = -1
                text = self.normal_resolutions[idx+1]
            else:
                idx = self.wide_resolutions.index(item["text"])
                if idx == len(self.wide_resolutions) -1:
                    idx = -1
                text = self.wide_resolutions[idx+1]
            
            item["text"] = text
        elif item is self.qualityButton:
            if item["text"] is _t("options_video_quality_normal"):
                item["text"] = _t("options_video_quality_high")
            else:
                item["text"] = _t("options_video_quality_normal")
                
    def destroy(self):        
        if self._hasChanged:
            options = {}
            options["options_fullscreen"] = str(self.fsCheckBox["indicatorValue"])
            if self.aspectButton["text"] == _t("options_aspect_normal"):
                options["options_aspect"] = "options_aspect_normal"
            else:
                options["options_aspect"] = "options_aspect_wide"
            
            options["options_resolution"] = self.resolutionButton["text"]
            
            
            if self.qualityButton["text"] == _t("options_video_quality_normal"):
                options["options_video_quality"]="options_video_quality_normal"
            else:
                options["options_video_quality"]="options_video_quality_high"
            
            cfg.setMultipleStrValuesForKey(options)
        
        DirectFrame.destroy(self)
                
