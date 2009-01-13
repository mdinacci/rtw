# -*- coding: utf-8-*-

"""
Author: Marco Dinacci <dev@dinointeractive.com>
Copyright © 2008-2009

Events from the game and the editor.
"""

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

DELETE_NODE="delete-node"
SELECT_ENTITY="select-entity"
# EDITOR ONLY EVENTS END   ===============