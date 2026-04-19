from HardwarePlatform import Display, sleep, button_a, pin2, ticks_ms, PI, i2c
from calibrateFactors import CalibrateFactors
from senzors import LineSituationEnum
from lightSubsystem import BeamsEnum
from robot import createRobotJoyCar
from directions import DirectionEnum
from SM import CPU, Step, Task
from SMcrossRoads import CrossRoads
from position import Position
from timer import Timer

from time import sleep
from picoed import button_a
import pwmio
from board import P1, LED

if __name__ == "__main__": 

    robot = None
    try:
        print("code:Start")
        Display.clear()
        Display.supplyVoltage()
        Display.redraw()
        sleep(2000)
        Display.clear()

        robot = createRobotJoyCar()
        # robot.motionControl.calibration(pwmFrom=70, pwmTo=210, pwmSkip=5)

        robot.motionControl.stopRegulatePwm()
        # robot.tempomat.distance = 0.2
        stateMachine = CrossRoads(robot)
        CPU.add(stateMachine)

        while not button_a.was_pressed():
            CPU.tick()
            robot.update()
            Display.updatePixels()
            
        print("code:Stop")
        robot.stop()
    except Exception as e:
        print('Emergency stop!')
        if robot is not None:
            robot.emergencyShutdown()
        raise e
