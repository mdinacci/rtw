"""
        verts = [
         {'node':None, 'point': (-7.5, -8., 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (5., -8.3,- 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7.5, -8, 0.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-9.8, -2.7, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-5.3, -7.2, -3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (5.3, -7.2, -3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (9.8, -2.7, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-11., 4.0, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (-6., -1.8, 3.), 'color' : (0,1,0,0)} ,
         {'node':None, 'point': (6., -1.8, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (11, 4.0, 3.), 'color' : (0,0.5,0,0)} ,
         {'node':None, 'point': (-9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (-7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (7., 7.8, 3.), 'color' : (0,0,0,0)} ,
         {'node':None, 'point': (9.5, 9.5, -3.), 'color' : (0,0,0,0)} ,
         ]
        verts = [
                 {'node':None, 'point': (3, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (6, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (9, 0, 0), 'color' : (0,0,0,0)} ,
                 {'node':None, 'point': (12, 0, 0), 'color' : (0,0,0,0)} ,
                 
                 {'node':None, 'point': (3, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (6, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (9, 3, 0), 'color' : (0,1,0,0)} ,
                 {'node':None, 'point': (12, 3, 0), 'color' : (0,1,0,0)} ,
                 
                 {'node':None, 'point': (3, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (6, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (9, 6, 0), 'color' : (0,0,1,0)} ,
                 {'node':None, 'point': (12, 6, 0), 'color' : (0,0,1,0)} ,
                 
                 {'node':None, 'point': (3, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 10, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 10, 0), 'color' : (0,1,1,0)}
                 ,
        
                 {'node':None, 'point': (3, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 12, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 12, 0), 'color' : (0,1,1,0)},
                 
                 {'node':None, 'point': (3, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (6, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (9, 14, 0), 'color' : (0,1,1,0)} ,
                 {'node':None, 'point': (12, 14, 0), 'color' : (0,1,1,0)}
         ]
         """
        
#============================================
loader.loadModelCopy("models/misc/xyzAxis").reparentTo(render)

def displayLines(a,b, actor):
        np = actor.render.nodepath
        lines = LineNodePath(parent = np, thickness = 4.0, colorVec = Vec4(1, 0, 0, 1))
        lines.reset()
        
        if actor.physics.geomType == Types.Geom.SPHERE_GEOM_TYPE:
            halfHeight = actor.physics.radius / 2.0
            halfLen = halfHeight
            leng = actor.physics.radius
        else:
            halfLen = actor.physics.length / 2.0
            halfHeight = actor.physics.height  / 2.0
            leng = actor.physics.length
            
        lines.drawLines([((a[0]-leng, a[1]+halfLen-leng, a[2]),
                          (b[0]-leng, a[1]+halfLen-leng, a[2]),
                          (b[0]-leng, a[1]-halfLen-leng, a[2]),
                          (a[0]-leng, a[1]-halfLen-leng, a[2]),
                          (a[0]-leng, a[1]+halfLen-leng, a[2]))])
        lines.create()
        
        lines = LineNodePath(parent = np, thickness = 4.0, colorVec = Vec4(0, 0, 1, 1))
        lines.reset()
        lines.drawLines([((a[0], a[1]+halfLen, b[2]),
                          (b[0], a[1]+halfLen, b[2]),
                          (b[0], a[1]-halfLen, b[2]),
                          (a[0], a[1]-halfLen, b[2]),
                          (a[0], a[1]+halfLen, b[2]))])
        lines.create()

"""
    def changeNature(self, nature):
        newCell = loader.loadModel("cell_%s" % nature.lower())
        if newCell is not None:
            logger.info("Changing cell nature to: %s" % nature)
            newCell.setScale(self._nodePath.getScale())
            newCell.setPos(self._nodePath.getPos())
            parent = self._nodePath.getParent()
            newCell.setTag("pos",self._nodePath.getTag("pos"))
            newCell.setColor(self._nodePath.getColor())
            self._nodePath.removeNode()
            
            newCell.reparentTo(parent)
            self._nodePath = newCell
        else:
            logger.error("Cannot change nature cell to: %s. Model does not \
            exist." % nature )
"""    
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
                
def displayLinesAroundObject():
            lines = LineNodePath(parent = masterNode, thickness = 5.0, colorVec = Vec4(1, 0, 0, 1))
            lines.reset()
            
            np = cell.getNodePath()
            halfLen = Cell.LENGTH/2
            halfHeight = Cell.HEIGHT/2
            lines.drawLines([((np.getX()-halfLen, np.getY()-halfLen, np.getZ()-halfHeight),
                              (np.getX()+halfLen, np.getY()-halfLen, np.getZ()-halfHeight),
                              (np.getX()+halfLen, np.getY()+halfLen, np.getZ()-halfHeight),
                              (np.getX()-halfLen, np.getY()+halfLen, np.getZ()-halfHeight),
                              (np.getX()-halfLen, np.getY()-halfLen, np.getZ()-halfHeight))])
            lines.drawLines([((np.getX()-halfLen, np.getY()-halfLen, np.getZ()+halfHeight),
                              (np.getX()+halfLen, np.getY()-halfLen, np.getZ()+halfHeight),
                              (np.getX()+halfLen, np.getY()+halfLen, np.getZ()+halfHeight),
                              (np.getX()-halfLen, np.getY()+halfLen, np.getZ()+halfHeight),
                              (np.getX()-halfLen, np.getY()-halfLen, np.getZ()+halfHeight))])
            
            lines.create()
