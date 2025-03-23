from HardwarePlatform import I2C_ADDR_MOTION, i2c
from directions import DirectionEnum

class Engine:
    # Třída implementující motor
    def __init__(self, place:int) -> None:
        self.__place = place
        self.__pwm = 0
        self.__pwmNo_Back = None
        self.__pwmNo_Forw = None
        if place == DirectionEnum.RIGHT:
            self.__pwmNo_Back = 2
            self.__pwmNo_Forw = 3
        elif place == DirectionEnum.LEFT:
            self.__pwmNo_Back = 4
            self.__pwmNo_Forw = 5
        self.initDriver()

    def initDriver(self) -> None:
        # inicializuj pwm driver pro motor
        i2c.init(freq=400_000)
        i2c.write(I2C_ADDR_MOTION, bytes([0, 0x01]))
        i2c.write(I2C_ADDR_MOTION, bytes([8, 0xAA]))

    def writePWM(self, pwm:int) -> None:
        # omezeni pwm (zapisujeme 1 byte = maximalne 255 ve spravnem smeru)
        if pwm > 255:
            pwm = 255
        if pwm < -255:
            pwm = -255
        self.__pwm = pwm
        
        if pwm >= 0:
            pwmNo_off = self.__pwmNo_Back
            pwmNo_on = self.__pwmNo_Forw
        else:
            pwmNo_off = self.__pwmNo_Forw
            pwmNo_on = self.__pwmNo_Back

        # zapiš pwm přes i2c do motoru
        if (pwmNo_off is not None) and (pwmNo_on is not None):
            i2c.write(I2C_ADDR_MOTION, bytes([pwmNo_off, 0]))
            i2c.write(I2C_ADDR_MOTION, bytes([pwmNo_on, abs(pwm)]))

    def stop(self) -> None:
        self.writePWM(0)

    def emergencyShutdown(self) -> None:
        try:
            self.stop()
        except Exception as e:
            pass
