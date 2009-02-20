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
