# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Events from the game and the editor.
"""

GAME_START="start-game"
GAME_EXIT="exit-game"
GAME_DESTROY="destroy-game"

END_TRACK="end-track"



#NEW_ACTOR="new-actor"
REQUEST_SHUTDOWN="request_shutdown"
MOVE_PLAYER="move-player"

# EDITOR ONLY EVENTS BEGIN ===============
CHANGE_NATURE="change-nature"
SWITCH_VIEW="switch-view"
NEW_ROW="new-row"
EDIT_NODE="edit-node"
MOUSE_ENTER_PANDA="mouse-enter-panda"
MOUSE_LEAVE_PANDA="mouse-leave-panda"
# sent by Scene that act as a model for the GUI. Received by Logic
DELETE_ENTITY_GUI="delete-entity-gui"

ENTITY_DELETED="entity-deleted"
SELECT_ENTITY="select-entity"
ENTITY_ADDED="entity-added"
ENTITY_MODIFIED="entity-modified"
ENTITY_PROPERTY_MODIFIED="entity-property-modified"
# EDITOR ONLY EVENTS END   ===============