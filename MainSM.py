from HardwarePlatform import ticks_ms, sleep, PI
from directions import DirectionEnum
from SM import AbstractSM, Task, Step
from robot import Robot

class MainSM(AbstractSM):

    STEPdopredu = Step('dopredu')
    STEPdozadu = Step('dozadu')
    STEPvpravo = Step('vpravo')
    STEPvlevo = Step('vlevo')

    taskList = [
        STEPvpravo,
        STEPvlevo,
        STEPdozadu,
        STEPdopredu,
    ]
    
    def __init__(self, robot: Robot, tasks=None, tick_time=None) -> None:
        self.__robot = robot
        super().__init__(tasks, tick_time)
        self.debug = True

    def __stop(self):
        self.__robot.motionControl.stop()
        sleep(100)

    def __dopredu(self):        
        self.__robot.motionControl.newVelocity(0.1, 0)

    def __dopredu__done(self):
        self.__stop()

    def __dozadu(self):
        self.__robot.motionControl.newVelocity(-0.1, 0)

    def __dozadu__done(self):
        self.__stop()

    def __vlevo(self):
        self.__robot.lightsControl.indicator.direction = DirectionEnum.LEFT
        self.__robot.motionControl.newVelocity(0, PI/8)

    def __vlevo__done(self):
        self.__robot.lightsControl.indicator.direction = None
        self.__stop()

    def __vpravo(self):
        self.__robot.lightsControl.indicator.direction = DirectionEnum.RIGHT
        self.__robot.motionControl.newVelocity(0, -PI/8)

    def __vpravo__done(self):
        self.__robot.lightsControl.indicator.direction = None
        self.__stop()
