import direct.directbase.DirectStart
from pandac.PandaModules import *
from direct.filter.CommonFilters import CommonFilters
import sys


base.accept("escape", sys.exit)
base.disableMouse()
base.oobe()

base.accept("v", base.bufferViewer.toggleEnable)
base.accept("V", base.bufferViewer.toggleEnable)
base.bufferViewer.setPosition("llcorner")
base.bufferViewer.setLayout("hline")

track = loader.loadModel("track.bam")
track.reparentTo(render)
track.setPos(Point3(0,0,0))

dlight = DirectionalLight('dlight')
alight = AmbientLight('alight')
dlnp = track.attachNewNode(dlight)
alnp = track.attachNewNode(alight)
dlight.setColor(Vec4(0.8, 0.7, 0.4, 1))
alight.setColor(Vec4(0.2, 0.2, 0.2, 1))
dlnp.setHpr(0, -60, 0)
track.setLight(dlnp)
track.setLight(alnp)

render.setShaderAuto()
filters = CommonFilters(base.win, base.cam)
#filters.setCartoonInk(separation=50)
filters.setBloom(blend=(0.1,0.1,0.9,0), desat=-0.5, intensity=2.0)

run()
