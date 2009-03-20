# FSAA 
from pandac.PandaModules import loadPrcFileData
loadPrcFileData('', 'multisamples 16')
render.setAntialias(AntialiasAttrib.MAuto)


os.getenv('SystemDrive') # on windows
"""
        rbc = RigidBodyCombiner("rbc")
        rbcnp = NodePath(rbc)
        rbcnp.reparentTo(self.view._rootNode)
        self.track.nodepath.reparentTo(rbcnp)
        rbc.collect()
        """
        """
        colour = (0.5,0.8,0.8)
        expfog = Fog("Scene-wide exponential Fog object")
        expfog.setColor(*colour)
        expfog.setExpDensity(0.008)
        self.track.nodepath.setFog(expfog)
        base.setBackgroundColor(*colour)
        """
        
#self.env.nodepath.hprInterval(2000, Point3(360, 0,0)).loop()

import sys

def enable_vsync():
    if sys.platform != 'darwin':
        return
    try:
        import ctypes
        import ctypes.util
        ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))
        # set v to 1 to enable vsync, 0 to disable vsync
        v = ctypes.c_int(1)
        ogl.CGLSetParameter(ogl.CGLGetCurrentContext(), ctypes.c_int(222), ctypes.pointer(v))
    except:
        print "Unable to set vsync mode, using driver defaults"
# forward vector of the ball expressed in the world coordinate space 
        #forward = self.ball.nodepath.getParent().getRelativeVector(self.player.nodepath,
        
# convert textures to internal optimized format
#egg2bam -txo -ctex model.egg -o model.bam
        
"""self.cameraRay = CollisionSegment()

a = self.player.nodepath.getPos()
b = base.camera.getPos()
c = math.sqrt(b.getY()**2 + (a.getY() - b.getY()) **2) + \
                                                self.cam.TARGET_DISTANCE
p = Point3(a-b)
p.setY(c)
self.cameraRay.setPointA(Point3(0,0,0))
self.cameraRay.setPointB(p)
"""
#steering = 7
            #right.setZ(0)
            #right.normalize()
            #self.player.nodepath.setPos(self.player.nodepath.getPos() + (right*steering*dt))
self.velocityVector = self.model.getQuat().getForward() * self.speed 


# to know which texture is bind to a GeomNode
for i in range(geomNode.getNumGeoms()):
  state = geomNode.getGeomState(i)
  texAttrib = state.getAttrib(TextureAttrib.getClassType())
  if texAttrib:
    tex = texAttrib.getTexture()
    print i, tex
    
#============================================
loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)


#from pandac.PandaModules import ClockObject
#FPS = 30
#globalClock = ClockObject.getGlobalClock()
#globalClock.setMode(ClockObject.MLimited)
#globalClock.setFrameRate(FPS)

#if not base.mouseWatcher.node().hasMouse(): return Task.cont
#      m=base.mouseWatcher.node().getMouse() 
#self.dta += globalClock.getDt()
            #while self.dta > self.REFRESH_RATE:
            #    self.dta -= self.REFRESH_RATE
                # run all processes
