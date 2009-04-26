# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Game events.
"""

GAME_START="start-game"
GAME_EXIT_REQUEST="exit-game-request"
GAME_DESTROY="destroy-game"

END_TRACK="end-track"
TOGGLE_SOUND="toggle-sound"
OPTIONS_MENU_REQUEST="options-menu-request"
PROFILE_MENU_REQUEST="profile-menu-request"
OPTIONS_RESET="options-reset"
ACTIVATE_ONLINE_MODE="activate-online-mode"
DESACTIVATE_ONLINE_MODE="desactivate-online-mode"
RESTART_TRACK="restart_track"
QUIT_TRACK="quit-track"
UNPAUSE_GAME="unpause-game"
BALL_SELECTED="ball-selected"
TRACK_SELECTED="track-selected"
GAME_MODE_SELECT="game-mode-select"

# collision events
BALL_INTO = "ray-into-%in"
BALL_INTO_CHECKPOINT="ray-into-cp"
BALL_INTO_SLOW="ray-into-slow"
BALL_INTO_ACCELERATE="ray-into-accelerate"
BALL_INTO_JUMP="ray-into-jump"

# timer
TIME_OVER="time_over"