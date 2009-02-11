def generateVertexes(self, grid, x=0,y=0,z=0):
        stepOut = False
        
        for i,row in enumerate(grid):
            for j,col in enumerate(row):
                # iterate the row until we find a column which is not None
                if col is not None:
                    tileRow = []
                    # read 5 (maximum number of tiles per row) +1 columns
                    # HACK change with constants from tileeditorview
                    tileRow = [grid[i][j+w] for w in range(5+1) if (j+w) < 80]
                    tileRow = filter(lambda x: x is not None, tileRow)
                    
                    if len(tileRow) > 0:
                        # detect if there is a curve (direction changes)
                        isCurve = False
                        curveOffset = 0
                        firstDir = tileRow[0].direction
                        for tile in tileRow:
                            if tile.direction != firstDir:
                                isCurve = True
                                curveDir = tile.direction
                                curveOffset = grid[i].index(tile)
                                break
                            
                        if isCurve:
                                
                            logger.debug("Detected a curve, direction is: %s" \
                                         % tile.direction)
                            
                            # TODO interpolate some vertexes to make the 
                            # curve smoother
                            
                            # transpose matrix
                            newgrid = deepcopy(grid)
                            newgrid.reverse()
                            newgrid = map(lambda *row: list(row), *grid)[curveOffset:]
                            
                            # call generate with the new matrix
                            self.generateVertexes(newgrid)
                            stepOut = True
                            
                        else:
                            self.addVertexes(tileRow, self.tempVertexes)
                    # read another row
                    break
            if stepOut:
                break

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
