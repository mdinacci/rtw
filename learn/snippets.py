# CONFIG VARIABLES DEV:
# want-dev 1
# want-pstats
# pstats-tasks
# task-timer-verbose
# track-gui-items
# 
# CONFIG VARIABLES MISC:
# playback-session
# record-session
#
#

lines = LineNodePath(parent = render, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
def drawLines():
  # Draws lines between the smiley and frowney.
  lines.reset()
  lines.drawLines([((frowney.getX(), frowney.getY(), frowney.getZ()),
                    (smiley.getX(), smiley.getY(), smiley.getZ())),
                   ((smiley.getX(), smiley.getY(), smiley.getZ()),
                    (0, 0, 0))])
  lines.create()


