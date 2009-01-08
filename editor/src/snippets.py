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
            
class A():
    a = "1"
    b = "2"
    c = {"z":"1"}
    def __getattr__(self,attr):
        print "IN ATTR"
        try:
            return self.__dict__[attr]
        except KeyError, e:
           return self.c[attr] 
        
        
a = A()
print a.a,a.b,a.z

def save_canvas(self):
        from os import environ
        chooser = gtk.FileChooserDialog(title=None,
                                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
        buttons=(gtk.STOCK_CANCEL, 
                 gtk.RESPONSE_CANCEL, 
                 gtk.STOCK_SAVE,
                 gtk.RESPONSE_OK))
        chooser.set_current_folder("%s" % environ['HOME'])

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            if '.' in filename:
                filename = filename[:filename.index('.')] + ".track"
            else:
                filename = filename + ".track"

        chooser.destroy() 
        self.presenter.set_track_filename(filename)

class SlopeEditorController: pass

class SlopeEditorCanvas(gtk.DrawingArea):
    
    _pixmap = None # backing pixmap where the drawing is performed
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
        self.set_sensitive(True)
        self.set_double_buffered(False) # redundant because of _pixmap
        self.add_events(gtk.gdk.BUTTON_RELEASE_MASK |
                                gtk.gdk.BUTTON1_MOTION_MASK |
                                gtk.gdk.POINTER_MOTION_HINT_MASK |
                                gtk.gdk.BUTTON_PRESS_MASK |
                                gtk.gdk.KEY_PRESS_MASK |
                                gtk.gdk.KEY_RELEASE_MASK
                                )

        self.connect("expose_event", self._on_expose)
        self.connect("configure_event", self._on_configure)

        #self.controller = SlopeEditorController(self)
        
        
    def _on_configure(self, widget, event):
        """ GTK callback """
        x, y, width, height = widget.get_allocation()
        self._pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self._pixmap.draw_rectangle(widget.get_style().white_gc,
                          True, 0, 0, width, height)
        return True
    
    def _on_expose(self, widget, event):
        """ GTK callback """
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self._pixmap, x, y, x, y, width, height)
        if self._pixmap != None:
            pass # FIXME redraw track !

        return False


class FreeHandCanvas(gtk.DrawingArea, Observer):
    """ This is the canvas where the track is sketched """
    
    _pixmap = None # backing pixmap where the drawing is performed
    
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        Observer.__init__(self)
        
        self.set_sensitive(True)
        self.set_double_buffered(False) # redundant because of _pixmap
        self.add_events(gtk.gdk.BUTTON_RELEASE_MASK |
                                gtk.gdk.BUTTON1_MOTION_MASK |
                                gtk.gdk.POINTER_MOTION_HINT_MASK |
                                gtk.gdk.BUTTON_PRESS_MASK |
                                gtk.gdk.KEY_PRESS_MASK |
                                gtk.gdk.KEY_RELEASE_MASK
                                )

        self.connect("expose_event", self._on_expose)
        self.connect("configure_event", self._on_configure)
        self.connect('motion_notify_event', self._on_motion_notify)
        self.connect('button_release_event', self._on_button_release)
        self.connect('button_press_event', self._on_button_press)
        self.connect('key_press_event', self._on_key_press)

        self.controller = FreeHandController(self)
        
        # register with track in order to get notified in case of modifications
        track.register(self)
    
    def update(self):
        """ 
        Track has changed, update the drawing. 
        Supports only adding new points, one at a time  
        """
        point = self.controller.get_latest_points(1)[0]
        self.draw_brush(point[0], point[1])
        
    def draw_brush(self, x, y, w = 6, h = 6):
        """ Draw a rectangle on the canvas """
        rect = (int(x-w/2), int(y-h/2), w, h)
        self._pixmap.draw_rectangle(self.get_style().black_gc, True,
                              rect[0], rect[1], rect[2], rect[3])
        self.queue_draw_area(rect[0], rect[1], rect[2], rect[3])

    def _on_configure(self, widget, event):
        """ GTK callback """
        x, y, width, height = widget.get_allocation()
        self._pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self._pixmap.draw_rectangle(widget.get_style().white_gc,
                          True, 0, 0, width, height)
        # TODO draw grid
        
        cell_size = 10
        lines_gc = self._pixmap.new_gc()
        main_lines_gc = self._pixmap.new_gc()    
        lines_gc.set_foreground(self._pixmap.get_colormap().alloc_color(50000,50000,50000))
        main_lines_gc.set_foreground(self._pixmap.get_colormap().alloc_color(65535,0,0))

        # draw columns
        for i in range(0,int(width/cell_size)+1):
            gc = None
            if i % 5 == 0:
                gc = main_lines_gc
            else:
                gc = lines_gc
                
            self._pixmap.draw_lines(gc,
                                    [(i*cell_size,0), (i*cell_size,height)])
        
        # draw lines
        for i in range(0, int(height/cell_size)+1):
            gc = None 
            if i % 5 == 0:
                gc = main_lines_gc
            else:
                gc = lines_gc
                
            self._pixmap.draw_lines(gc,
                                    [(0,i*cell_size), (width,i*cell_size)])
        
        return True
    
    def _on_expose(self, widget, event):
        """ GTK callback """
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                self._pixmap, x, y, x, y, width, height)
        if self._pixmap != None:
            pass # FIXME redraw track !

        return False

    def _on_key_press(self, widget, event):
        print dir(event)

    def _on_motion_notify(self, widget, event):
        """ GTK callback """
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
    
        if state & gtk.gdk.BUTTON1_MASK and self._pixmap != None:
            self.controller.keep_drawing(event)

        return True

    def _on_button_press(self, widget, event):
        """ GTK callback """
        if event.button == 1 and self._pixmap != None:
            self.controller.start_drawing(event)
        return True

    def _on_button_release(self, widget, event):
        """ GTK callback """
        if event.button == 1 and self._pixmap != None:
            self.controller.stop_drawing(event)
        return True

class FreeHandController(object):
    def __init__(self, canvas):
        super(FreeHandController, self).__init__()
        self.canvas = canvas

    def _add_coord(self, coord):
        track.add_coord(coord)

    def start_drawing(self, event):
        track.is_drawing = True
        self._add_coord(event.get_coords())
        
    def keep_drawing(self, event):
        self._add_coord(event.get_coords())
    
    def stop_drawing(self, event):
        track.is_drawing = False
    
    def get_points(self):
        return track.get_xy_coords()
    
    def get_latest_points(self, qty):
        return track.get_latest_coords(qty)
    

class Editor(object):
    """
    The editor is basically a world editor, specialized for the 
    SpeedBlazer game. It allows to construct the games by managing 3D objects,
    it allows also to debug and test the game.
    """
    FPS = 1.0/70.0
    
    def __init__(self):
        self.world = World()

        self.ins = SafeDirectObject()
        self._setupInput()
        
        # if want-directtols is true, don't activate all the modes
        if wantsDirectTools():
            self.modes = {"debug": DebugMode(self.world)}
            self.mode = self.modes["debug"]
        else:
            self.modes = {"roam": RoamMode(self.world), 
                          "edit": EditMode(self.world),
                          "drive":DriveMode(self.world)}
            self.mode = self.modes["roam"]
            
        self.mode.enable()
        
        self.isRunning = True
        
        # create automatically some geometry to speed up work
        track = self.world.getTrack()
        for i in range(0,10):
            track.addRow()
            
        #for cell in track.getCells():
        #    self.world.addEntity(cell)
    
    def _dumpNodes(self):
        render.ls()
        self.isRunning = False
    
    def save(self):
        def saveRecursive(parent, eggParentData, relativeTo):
            pdir(parent.getChildren())
            for child in parent.getChildren().asList():
                # save the childs data
                modelData = None
                if child.hasTag(ENABLE_SCENEGRAPHBROWSER_MODEL_TAG):
                  objectId = child.getTag(EDITABLE_OBJECT_TAG)
                  object = modelIdManager.getObject(objectId)
                  modelData = object.getSaveData(relativeTo)
                  eggParentData.addChild(modelData)
                # if there is data of the model walk the childrens
                if modelData:
                  # search childrens
                  saveRecursiveChildrens(child, modelData, relativeTo)
                  
        eggData = EggData()
        eggData.setCoordinateSystem(1)
        relativeTo = Filename("/tmp/test.egg").getDirname()
        relativeTo = str(Filename.fromOsSpecific(relativeTo))
        saveRecursive(render, eggData, relativeTo)
        # save the egg file
        eggData.writeEgg(Filename(filepath))
        print "egg file saved to disk"
    
    def _setupInput(self):
        inputManager.bindCallback("escape", self.quit, scheme="base")
        inputManager.bindCallback("m", self.save, scheme="base")
        
        if not wantsDirectTools():
            inputManager.bindCallback("1", self._switchMode, ["roam"], scheme="base")
            inputManager.bindCallback("2", self._switchMode, ["edit"], scheme="base")
            inputManager.bindCallback("3", self._switchMode, ["drive"], scheme="base")
            inputManager.bindCallback("4", self._switchMode, ["debug"], scheme="base")
            inputManager.bindCallback("9", self._dumpNodes, scheme="base")
        
    @pandaCallback
    def _switchMode(self, mode):
        if mode in self.modes.keys():
            if self.mode != self.modes[mode]:
                logger.info("switching to %s mode" % mode)
                self.mode.disable()
                self.mode = self.modes[mode]
                self.mode.enable()
        else:
            logger.error("Mode %s doesn't exists" % mode)
    
    def quit(self):
        self.isRunning = False
    
    def run(self):
        from time import sleep
        while self.isRunning:
            #self._input.update()
            taskMgr.step()
            inputManager.update()
            sleep(self.FPS)
        else:
            render.analyze()
            # TODO do cleanup
            logger.info("Quitting application, have fun")

 
class World(object):
    """
    The world contains and manage (by delegating) everything in the 3D world
    It is made of few 3D important objects:
    - a Track (actually a collection of cells)
    - a Ball, or more generally the user character
    - an Environment, consisting of the background scene and objects
    
    The world also contains other 3D objects that can interact with the
    player.
    
    The HUD is also managed by the world.
    
    TODO store the list of entities in the EntityManager 
    TODO to extends from GameView
    """
    def __init__(self):
        self.input = SafeDirectObject()
        self.input.accept("new-entity", self.addEntity)

        self._entities = []
        # setup the environment and the lights
        self.physMgr = PhysicManager(self)
        self._prepareWorld()
        
        self._track = Track(masterNode)
        self.addEntity(self._track)
        
        self._ball = TheBall(masterNode, Point3(4,2,5))
        self._ball.geom = self.physMgr.createGeomForActor(self._ball)
        self.addEntity(self._ball)
        self._ball.nodepath.hide()
        # just in case there is no track yet, otherwise the ball would fall
        # forever 
        # FIXME getBody is deprecated
        self._ball.geom.getBody().setGravityMode(False)
        
    @traceMethod
    def addEntity(self, entity):
        self._entities.append(entity)
        #if isinstance(entity, GameActor):
            # FIXME shouldn't the Actor create the body itself ?
        #    entity.geom = self.physMgr.createGeomForActor(entity)
        logger.debug("Added new entity in the world %s" % entity)
        
    def getTrack(self):
        return self._track
    
    def getBall(self):
        return self._ball
    
    def getActors(self):
        # TODO this loop can be computed only if we add a new entity
        # evaluate time/space 
        actors = []
        for entity in self._entities:
            if isinstance(entity, GameActor):
                actors.append(entity)
                
        return actors
    
    def _setupLights(self):
        #Create some lights and add them to the scene. By setting the lights on
        #render they affect the entire scene
        #Check out the lighting tutorial for more information on lights
        lAttrib = LightAttrib.makeAllOff()
        ambientLight = AmbientLight( "ambientLight" )
        ambientLight.setColor( Vec4(.4, .4, .35, 1) )
        lAttrib = lAttrib.addLight( ambientLight )
        directionalLight = DirectionalLight( "directionalLight" )
        directionalLight.setDirection( Vec3( 0, 8, -2.5 ) )
        directionalLight.setColor( Vec4( 0.9, 0.8, 0.9, 1 ) )
        lAttrib = lAttrib.addLight( directionalLight )
        render.attachNewNode( directionalLight.upcastToPandaNode() )
        render.attachNewNode( ambientLight.upcastToPandaNode() )
        render.node().setAttrib( lAttrib )
        
    def _prepareWorld(self):
        env = Environment(masterNode, Point3(-8,42,-5))
        self._entities.append(env)    
        self._setupLights()
    
        
class AbstractEditorMode(object):
    """ 
    An AbstractEditorMode allows to use the editor in different ways in order
    to construct the world, test the game, debugging it etc...
    Each mode has its own set of input bindings and a different camera. 
    """
    def __init__(self, world):
        self.world = world
        self._setupCamera()
        self._setupInput()
    
    def enable(self):
        self.camera.enable()
        inputManager.switchSchemeTo(self._inputScheme)
        
    def disable(self):
        self.camera.disable()
        #self.input.ignoreAll()
        
    def _setupCamera(self):
        raise NotImplementedError
    
    def _setupInput(self):
        raise NotImplementedError

    
class DriveMode(AbstractEditorMode):
    """ 
    This mode is used to simulate the game 
    
    Accepted inputs:
    - i -> move ball forward
    - j -> move ball left
    - k -> move ball backward (slow down)
    - l -> move ball right
    """
    def __init__(self, world):
        super(DriveMode, self).__init__(world)
    
    def enable(self):
        super(DriveMode, self).enable()
        self.world.getBall().nodepath.show()
        # FIXME getBody is deprecated
        self.world.getBall().geom.getBody().setGravityMode(True)
    
    def disable(self):
        super(DriveMode, self).disable()
        self.world.getBall().nodepath.hide()
        # TODO
        #self.world.getBall().stop()
    
    def _setupCamera(self):
        # 3,3,-0.5 is the perfect setup to check the collision of the ball 
        # against the track
        self.camera = TheBallCamera(self.world.getBall(), 10, 14, 5)
        
    def _setupInput(self):
        self.__setupInput()
        
    def __setupInput(self):
        ball = self.world.getBall()
        self._inputScheme = "drive-mode"
        inputManager.createSchemeAndSwitch(self._inputScheme)
        inputManager.bindEvent("i", "ball-move", [0,1.5,0])
        inputManager.bindEvent("i-up", "ball-move", [0,0,0])
        inputManager.bindEvent("j", "ball-move", [-2,0,0])
        inputManager.bindEvent("j-up", "ball-move", [0,0,0])
        inputManager.bindEvent("k", "ball-move", [0,-0.5,0])
        inputManager.bindEvent("k-up", "ball-move", [0,0,0])
        inputManager.bindEvent("l", "ball-move", [2,0,0])
        inputManager.bindEvent("l-up", "ball-move", [0,0,0])


class DebugMode(AbstractEditorMode):
    """ 
    This mode is used in conjunction with the Panda3D
    direct-tools in order to debug the game. 
    
    It doesn't accept any input.
    """
    def __init__(self, world):
        super(DebugMode, self).__init__(world)
    
    def _setupCamera(self):
        self.camera = DebugCamera()
    
    def _setupInput(self):
        self._inputScheme = "debug-mode"
        inputManager.createSchemeAndSwitch(self._inputScheme)
    
    def disable(self):
        pass


class EditMode(AbstractEditorMode):
    """
    The EditMode is the most sophisticated mode. 
    It transform the editor in a world editor allowing to insert
    and to position objects.
    
    Accepted inputs:
    - space -> add a new cell
    - shift-space -> add a new row
    - mouse1 press -> select a cell
    """
    class PickedObjectState(object):
        color = BLACK = Vec4(0,0,0,1)
        index = -1
    
    class GUIControllerDelegate(object):
        def __init__(self, editMode):
            # Inner classes don't have access to the outer
            # class attributes like in Java :(
            self._editMode = editMode
        
        def __getattr__(self,attr):
            try:
                return self.__dict__[attr]
            except KeyError, e:
               return self._editMode.__dict__[attr]
        
        @pandaCallback
        def onDeleteButtonClick(self):
            if self._selectedObj is not None:
                logger.debug("Deleting selected entity %s: " % self._selectedObj)
                messenger.send("delete-entity", [self._selectedObj])
                np = self._selectedObj.nodepath
                np.hideBounds()
                np.removeNode()
                self._editMode._selectedObj = None
            else:
                logger.info("Nothing selected, cant' delete")
            
        @pandaCallback
        def onWorldButtonClick(self, selection):
            logger.debug("Selected %s" % selection)
            messenger.send("change-nature", [selection])
        
        @pandaCallback
        def onCellNatureClick(self, selection):
            logger.debug("Selected %s" % selection)
            if self._selectedObj is not None:
                self._selectedObj.changeNature(selection)
            #messenger.send("change-cell-nature", [selection])
            
            
    def __init__(self, world):
        super(EditMode, self).__init__(world)
        self._setupCollisionDetection()
        self._selectedObj = None
        self._gui = EditViewGUI(self.GUIControllerDelegate(self))
        self.disable()
        
    def enable(self):
        super(EditMode, self).enable()
        self._gui.enable()
        
    def disable(self):
        super(EditMode, self).disable()
        self._gui.disable()
        if self._selectedObj is not None:
            self._selectedObj.nodepath.hideBounds()
        self._selectedObj = None
    
    def __hasSelection(self):
        return hasattr(self, "pickedObjectState")
    
    #pandaCallback
    def _deleteCell(self, cell):
        logger.debug("Deleting cell: %s", cell)
    
    def __getClickedCellIdx(self):
        track = self.world.getTrack()
        trackNP = track.nodepath
        mousePos = base.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(base.camNode, mousePos.getX(), mousePos.getY())
        self.picker.traverse(trackNP)
        if self.pq.getNumEntries() > 0:
            self.pq.sortEntries()
            pickedObject = self.pq.getEntry(0).getIntoNodePath()
            row, col = map(lambda x: int(x), 
                           pickedObject.getTag("pos").split())
            idx = row*Track.ROW_LENGTH+col
            logger.debug("Selected object: %s at row,col: %d,%d (idx: %d)" % 
                         (pickedObject, row, col, idx ))
            
            return idx
        else:
            logger.warning("No intersection with track occurred, deleted cell?")
                
                
    @pandaCallback
    def _addRow(self):
        logger.debug("Adding row to track")
        self.world.getTrack().addRow()
        
    @pandaCallback
    def _addCell(self):
        logger.debug("Adding cell to track")
        self.world.getTrack().addCell()
        
    @pandaCallback
    def _onMousePress(self):
        if base.mouseWatcherNode.hasMouse():
            idx = self.__getClickedCellIdx()
            if idx != None:
                track = self.world.getTrack()
    
                if self.pq.getNumEntries() > 0:
                    if self.__hasSelection():
                        previousIndex = self.pickedObjectState.index
                        cell = track.getCellAtIndex(previousIndex)
                        cellNP = cell.nodepath
                        # the nodepath could have been deleted but its 
                        # place is always there in the scenegraph
                        if not cellNP.isEmpty():
                            cellNP.hideBounds()
                    else:
                        self.pickedObjectState = self.PickedObjectState()
                    
                cell = track.getCellAtIndex(idx)
                if self._selectedObj is not None and self._selectedObj == cell:
                    logger.info("Deselecting cell")
                    self._selectedObj.nodepath.hideBounds()
                    self._selectedObj = None
                else:
                    self._selectedObj = cell
                    np = self._selectedObj.nodepath
                    self.pickedObjectState.color = np.getColor()
                    self.pickedObjectState.index = idx
                
                    np.showBounds()
        else:
            logger.debug("No collisions at: %s" % mousePos)
            
    
    @pandaCallback
    def _onShiftMousePress(self):
        """ TODO """
        if self._selectedObj is None:
            self._onMousePress()
        else:
            idx = self.__getClickedCellIdx()
            row = idx / Track.ROW_LENGTH
            col = idx % Track.ROW_LENGTH
            prevIdx = self.pickedObjectState.index
            prevRow = idx / Track.ROW_LENGTH
            prevCol = idx % Track.ROW_LENGTH
            
            # TODO
            while prevIdx < idx:
                prevIdx += 1
            
            # get selected cell row col
            # get new cell row col
            #etc..
            
    
    def _setupCollisionDetection(self):
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue();
        self.pickerNode = CollisionNode("cellPickRay")
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pq)
        
    def _setupCamera(self):
        self.camera = FixedCamera()
        self.camera.setPos(0,-40,15)
        self.camera.lookAt(0,0,0)

    def _setupInput(self):
        self.__setupInput()

    def __setupInput(self):
        self._inputScheme = "edit-mode"
        inputManager.createSchemeAndSwitch(self._inputScheme)
        inputManager.bindCallback("space", self._addCell)
        inputManager.bindCallback("shift-space", self._addRow)
        inputManager.bindCallback("mouse1", self._onMousePress)
        inputManager.bindCallback("shift-mouse1", self._onShiftMousePress)

