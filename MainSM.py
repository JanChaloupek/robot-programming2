from HardwarePlatform import ticks_ms
from SM import AbstractSM, Task, Step
from robot import Robot
from LightSM import LightSM

class MainSM(AbstractSM):

    listTasks_Init=[
        Task()
    ]

    def __init__(self, robot: Robot, tasks, tick_time=None) -> None:
        self.__robot = robot
        super().__init__(tasks, tick_time)

    def __init(self):
        pass

