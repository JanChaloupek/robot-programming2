
from HardwarePlatform import sleep, button_a, pin2, ticks_ms, PI
from calibrateFactors import CalibrateFactors
from senzors import LineSituationEnum
from lightSubsystem import BeamsEnum
from robot import createRobotJoyCar
from directions import DirectionEnum
from systempicoed import System
from SM import CPU, Step, Task
from MainSM import MainSM
from position import Position
from timer import Timer


if __name__ == "__main__":

    robot = None
    try:
        print("code:Start")
        System.display_clear()
        # System.display_SupplyVoltage()
        # sleep(2000)
        # System.display_clear()

        robot = createRobotJoyCar()
        senzors = robot.getSenzors()
        robot.lightsControl.main = BeamsEnum.DippedBeams
        # robot.lightsControl.indicator.warning = True
        robot.motionControl.newVelocity(0.1, PI/8)
        robot.motionControl.stopRegulatePwm()
        # robot.tempomat.distance = 0.2

        stateMain = MainSM(robot, MainSM.taskList, tick_time=2_000)
        CPU.add(stateMain)

        # timer = Timer(timeout_ms=2000)
        while not button_a.was_pressed():
            CPU.tick()
            robot.update()
            sleep(1)
            
        print("code:Stop")
        robot.stop()
    except Exception as e:
        print('Emergency stop!')
        if robot is not None:
            robot.emergencyShutdown()
        raise e
