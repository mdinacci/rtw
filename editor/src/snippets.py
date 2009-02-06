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
def transpose(m):
    """
    Transpose the rectangular two-dimentional matrix m.
    """
    return [[m[y][x] for y in range(len(m))]for x in
range(len(m[0]))]


"""
s        color = (1,1,1,0)
        for i in range(10):
            vert = {'node':None, 'point': (i,0.875,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.625,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.375,z), 'color' : color}
            verts.append(vert)
            vert = {'node':None, 'point': (i,0.175,z), 'color' : color}
            verts.append(vert)
        verts = []
        vertexDistance = 2
        for row in tiles:
            realTiles = filter(lambda x: x is not None, row)
            if len(realTiles) > 0:
                firstTile = realTiles[0]
                lastTile = realTiles[-1]
                
                yIncrement = (lastTile.y -firstTile.y) / float(VERTEX_PER_ROW)
                if len(realTiles) == 1:
                    yIncrement = 1.0/ float(VERTEX_PER_ROW)
                for i in range(VERTEX_PER_ROW):
                    y = firstTile.y + (i * yIncrement) + yIncrement/2.0
                    x, z = firstTile.x, firstTile.z
                    # FIXME
                    color = self._colorForTile(realTiles[0].color)
                    vert = {'node':None, 'point': (x,y,z), 
                                    'color' : color}
                    verts.insert(0,vert)

"""
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
