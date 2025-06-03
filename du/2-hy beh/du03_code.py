from HardwarePlatform import sleep, i2c, I2C_ADDR_MOTION
from directions import DirectionEnum
from du03_engine import Engine

if __name__ == "__main__":

    pwm = 135
    engineLeft = None
    engineRight = None
    try:
        engineLeft = Engine(DirectionEnum.LEFT)
        engineRight = Engine(DirectionEnum.RIGHT)

        engineLeft.writePWM(pwm)
        engineRight.writePWM(pwm)
        sleep(1_000)
        engineLeft.stop()
        engineRight.stop()
        sleep(1_000)
        engineLeft.writePWM(-pwm)
        engineRight.writePWM(-pwm)
        sleep(1_000)
        engineLeft.stop()
        engineRight.stop()

    except Exception as e:
        print('Emergency stop!')
        if engineLeft is not None:
            engineLeft.emergencyShutdown()
        if engineRight is not None:
            engineRight.emergencyShutdown()
        raise e

