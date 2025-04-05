from HardwarePlatform import sleep, button_b
from directions import DirectionEnum
from du03_engine import Engine
from senzors import Senzors
from du06_SM import LineSM
from systempicoed import System
from SM import CPU

if __name__ == "__main__":
    leftEngine = None
    rightEngine = None
    try:
        print("code:Start")

        senzors = Senzors()
        leftEngine = Engine(DirectionEnum.LEFT)
        rightEngine = Engine(DirectionEnum.RIGHT)

        stateMain = LineSM(senzors, leftEngine, rightEngine)
        CPU.add(stateMain)

        while not button_b.was_pressed():
            CPU.tick()
            senzors.update()
            System.updatePixels()
            sleep(1)
            
        leftEngine.stop()
        rightEngine.stop()
        print("code:Stop")
    except Exception as e:
        print('Emergency stop!')
        if leftEngine is not None:
            leftEngine.emergencyShutdown()
        if rightEngine is not None:
            rightEngine.emergencyShutdown()
        print()
        print('Error:')
        raise e
