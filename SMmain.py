from HardwarePlatform import ticks_ms, sleep, PI
from directions import DirectionEnum
from SM import AbstractSM, Task, Step
from robot import Robot

class M_SM(AbstractSM):

    TASKmeasure = Task('measure')
    STEPwait = Step('wait')
    
    def __init__(self, robot: Robot, tasks=None, tick_time=None) -> None:
        self.__robot = robot
        super().__init__(tasks, tick_time)
        # self.debug = True

    def __start(self):
        self.nextTask(self.TASKmeasure)

    count = 0

    def __measure(self):        
        print('Distance=', self.__robot.getObstacleDistance(), self.__robot.__sonar.isError(), self.cpu_no)
        self.count += 1
        if self.count > 10:
            self.nextTask(self.STEPwait)

    def __wait(self):
        self.failureTask()
        

