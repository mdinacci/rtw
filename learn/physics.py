from direct.actor import Actor
from direct.task.Task import Task
from direct.directbase import DirectStart
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat, Point3, NodePath, PandaNode

import sys
from random import randint 

BLACK = Vec4(0,0,0,1)
WHITE = Vec4(1,1,1,1)
RED = Vec4(1,0,0,1)
GREEN = Vec4(0,1,0,1)
BLUE = Vec4(0,0,1,1)
HIGHLIGHT = Vec4(1,1,0.3,0.5)

colors = [BLACK,WHITE,RED,GREEN,BLUE]

class DaMan(Actor.Actor):
    _STEP = 0.03
    _isMoving = False
    _cmdMap = {"forward":0, "left":0, "backward":0, "right":0, "force":0}
    density = 950
    
    def __init__(self):
        super(DaMan, self).__init__('models/panda',{'walk':'models/panda-walk'}) 
        self.setScale(0.2)
        self.setPosHpr(0, 5, 10, 0, 0, 2)
        #self.setPosHpr(10, 1, 21, 0, 0, 2)
        self.reparentTo(render)
        
        self.accept("i", self._setCmd, ["forward"])
        self.accept("j", self._setCmd, ["left"])
        self.accept("k", self._setCmd, ["backward"])
        self.accept("l", self._setCmd, ["right"])
        self.accept("i-up", self._setCmd, ["forward", False])
        self.accept("j-up", self._setCmd, ["left", False])
        self.accept("k-up", self._setCmd, ["backward", False])
        self.accept("l-up", self._setCmd, ["right", False])
        self.accept("1", self._setCmd, ["force", False])

        taskMgr.add(self._moveTask, "move")
        
    def _setCmd(self, command, value=True):
        self._cmdMap[command] = value
        if value == True:
            self._isMoving = True
        else:
            self._isMoving = False

    def setPhysicBody(self, body):
        self.pbody = body

    def _moveTask(self, task):
        if self._isMoving:
            self.loop("walk", restart=0)
            if self._cmdMap["forward"]:
                self.setH(180)
                self.setY(self.getY() + self._STEP)
            elif self._cmdMap["left"]:
                self.setH(-90)
                self.setX(self.getX() - self._STEP)
            elif self._cmdMap["right"]:
                self.setH(90)
                self.setX(self.getX() + self._STEP)
            elif self._cmdMap["backward"]:
                self.setH(-180)
                self.loop("walk", restart=0)
                self.setY(self.getY() - self._STEP)
            elif self._cmdMap["force"]:
                self.applyForce = True
                
            self.pbody.setPosition(self.getPos())
            self.pbody.setQuaternion(self.getQuat())
        else:
            self.stop()
            
        return Task.cont
        
class Camera(DirectObject):
    """ Incapsulates the camera object to make its usage easier """

    def __init__(self):
        base.disableMouse()
        #base.camera.setPosHpr( 0, -15, 5.5, 0, 0, 0 )
        base.camera.setPos(40, 40, 20)
        base.camera.lookAt(0, 0, 0)
        #base.oobe()
        
        self.accept("w", self.moveForward)
        self.accept("s", self.moveBackward)
        self.accept("a", self.moveWest)
        self.accept("d", self.moveEast)

    def moveForward(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX(), p.getY()+4.0, p.getZ()))

    def moveBackward(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX(), p.getY()-4.0, p.getZ()))
        
    def moveWest(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX()-2, p.getY(), p.getZ()))
        
    def moveEast(self):
        p = camera.getPos()
        camera.setPos(Point3(p.getX()+2, p.getY(), p.getZ()))

class ThirdPersonCamera(DirectObject):
    def __init__(self, target):
        self.target = target
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        base.camera.setPos(target.getX(),target.getY()-20, 7) 
        base.disableMouse()
        taskMgr.add(self.cameraFollow,"cameraFollow") 

    def cameraFollow(self, task):
        base.camera.lookAt(self.target)
        camvec = self.target.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 10.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-10))
            camdist = 10.0
        if (camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - camvec*(5-camdist))
            camdist = 5.0
        
        self.floater.setPos(self.target.getPos())
        self.floater.setZ(self.target.getZ() + 2.0)
        self.floater.setY(self.target.getY() - 1.0)
        base.camera.lookAt(self.floater) 
        
        return Task.cont 


class World(DirectObject):
    # Create an accumulator to track the time since the sim
    # has been running
    deltaTimeAccumulator = 0.0
    # This stepSize makes the simulation run at 90 frames per second
    stepSize = 1.0 / 90.0
    objs = []
    
    def __init__(self):
        self.accept("escape", sys.exit)
        
        self._setupPhysics()

        panda = self._createPanda()
        #self.cam = ThirdPersonCamera(panda)
        self.cam = Camera()
        #self._createPlane()
        self._createSquarePlane()
        #self._createTrack()
        
        taskMgr.doMethodLater(.5, self._simulationTask, "Physics Simulation")

    def _setupPhysics(self):
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81)
        self.world.initSurfaceTable(1)
        # surfID1, surfID2, friction coeff, bouncy, bounce_vel, erp, cfm, slip, dampen (oscillation reduction) 
        self.world.setSurfaceEntry(0, 0, 150, 1.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
        
        self.space = OdeSimpleSpace()
        self.space.setAutoCollideWorld(self.world)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)

    def _createPlane(self):
        cm = CardMaker("ground")
        cm.setFrame(-10, 10, -10, 10)
        ground = render.attachNewNode(cm.generate())
        ground.setPos(0, 0, -1); ground.lookAt(0, 0, -2)
        ground.setColor(RED)
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, 0))
        groundGeom.setCollideBits(BitMask32(0x00000001))
        groundGeom.setCategoryBits(BitMask32(0x00000002))


    def _createSquarePlane(self):
        self.node = loader.loadModelCopy("models/square")
        self.node.setScale(30)
        self.node.setColor(GREEN)
        self.node.reparentTo(render)
        bodyGeom = OdeBoxGeom(self.space, 30, 30, 1)
        bodyGeom.setCollideBits(BitMask32(0x00000001))
        bodyGeom.setCategoryBits(BitMask32(0x00000002))
        bodyGeom.setPosition(self.node.getPos())

    def _createTrack(self):
        cols = 5
        rows = 120
    
        node = render.attachNewNode("track")
        self.squares = [None for i in range(0,cols*rows)]
        
        for row in range(0, rows):
            for col in range(0, cols):
                square = loader.loadModelCopy("models/square") 
                square.reparentTo(node)
                
                abs_idx = row*cols+col
                
                pos = Point3(( abs_idx % cols)-2, int( abs_idx / cols), 2)
                square.setPos(pos)
                square.setColor(colors[randint(0,len(colors)-1)])
                square.setTag("pos", "%d %d" % (row,col))
                self.squares[abs_idx] = square
         
                bodyGeom = OdeBoxGeom(self.space, 1, 1, 1)
                bodyGeom.setCollideBits(BitMask32(0x00000001))
                bodyGeom.setCategoryBits(BitMask32(0x00000002))
                bodyGeom.setPosition(pos)

    def _createPanda(self):
        daMan = DaMan()
        body = OdeBody(self.world)
        M = OdeMass()
        M.setSphere(daMan.density, 1.0)
        
        body.setMass(M)
        body.setPosition(daMan.getPos(render))
        body.setQuaternion(daMan.getQuat(render))

        boxGeom = OdeBoxGeom(self.space, 1, 1, 1)
        boxGeom.setCollideBits(BitMask32(0x00000002))
        boxGeom.setCategoryBits(BitMask32(0x00000001))
        boxGeom.setBody(body)

        # HACK 
        daMan.setPhysicBody(body)

        self.objs.append((daMan, body))
        return daMan
        
        
    # The task for our simulation
    def _simulationTask(self, task):
        # Add the deltaTime for the task to the accumulator
        self.deltaTimeAccumulator += globalClock.getDt()
        while self.deltaTimeAccumulator > self.stepSize:
            self.space.autoCollide()
            # Remove a stepSize from the accumulator until
            # the accumulated time is less than the stepsize
            self.deltaTimeAccumulator -= self.stepSize
            # Step the simulation
            self.world.quickStep(self.stepSize)
            
        # set the new positions
        for obj,body in self.objs:
            body.addForce(0,300,0)
            obj.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
            
        self.contactgroup.empty()
        
        return task.cont


    def main(self):
        run()
        

if __name__ == "__main__":
    w = World()
    w.main()

