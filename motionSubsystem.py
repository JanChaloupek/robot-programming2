from HardwarePlatform import i2c, I2C_ADDR_MOTION, ticks_ms, sleep
from calibrateFactors import CalibrateFactors
from speedMeasure import Encoder, MeasureUnit
from directions import DirectionEnum
from regulator import RegulatorP
from velocity import Velocity
from position import Odometry

from HardwarePlatform import I2C

class PCA9633:
    RegMODE1 = 0x00  # Mode 1 register
    RegMODE2 = 0x01  # Mode 2 register
    RegPWM0 = 0x02   # PWM register for channel 0
    RegPWM1 = 0x03   # PWM register for channel 1
    RegPWM2 = 0x04   # PWM register for channel 2
    RegPWM3 = 0x05   # PWM register for channel 3
    RegGRPPWM = 0x06  # Group duty cycle control
    RegGRPFREQ = 0x07  # Group frequency
    RegLEDOUT = 0x08  # LED output state
    RegSubADR1 = 0x09  # I2C-bus subaddress 1
    RegSubADR2 = 0x0A  # I2C-bus subaddress 2
    RegSubADR3 = 0x0B  # I2C-bus subaddress 3
    RegALLCALLADR = 0x0C  # AllCall I2C-bus address

    def __init__(self, i2c:I2C, address=0x62):
        self.__i2c = i2c
        self.__address = address

    def writeRegister(self, reg:int, value:int) -> None:
        # Write a value to a specific register
        self.__i2c.write(self.__address, bytes([reg, value]))
    
    def readRegister(self, reg:int) -> int:
        # Read a value from a specific register
        readbuffer = bytearray(1)
        self.__i2c.write_readinto(self.__address, bytes([reg]), readbuffer)
        return readbuffer[0]  # Return the read value

    def clearRegister_writeRegister(self, clearReg: int, writeReg:int, value:int, ) -> None:
        # Clear a register and then write a value to another register
        # This is useful for registers that require a specific sequence to clear before writing
        self.writeRegister(clearReg, 0)
        self.writeRegister(writeReg, value)
        # print('(', clearReg, '<=', 0, ',', writeReg, '<=', value, ')')

pca9633 = PCA9633(i2c)

class PCA9685:
    RegMODE1 = 0x00  # Mode 1 register
    RegMODE1_VALUE = 0x20
    RegMODE2 = 0x01  # Mode 2 register
    RegSubADR1 = 0x02  # I2C-bus subaddress 1
    RegSubADR2 = 0x03  # I2C-bus subaddress 2
    RegSubADR3 = 0x04  # I2C-bus subaddress 3
    RegALLCALLADR = 0x05  # AllCall I2C-bus address

    RegPwm00 = 0x06  # Pwm for channel 00  (On_L, On_H, Off_L, Off_H)
    RegPwm00_ON_L = 0x06  # All LED on register low byte
    RegPwm00_ON_H = 0x07  # All LED on register high byte
    RegPwm00_OFF_L = 0x08  # All LED off register low byte
    RegPwm00_OFF_H = 0x09  # All LED off register high byte
    RegPwm01 = 0x0A  # PWM for channel 01
    RegPwm02 = 0x0E  # PWM for channel 02
    RegPwm03 = 0x12  # PWM for channel 03
    RegPwm04 = 0x16  # PWM for channel 04
    RegPwm05 = 0x1A  # PWM for channel 05
    RegPwm06 = 0x1E  # PWM for channel 06
    RegPwm07 = 0x22  # PWM for channel 07
    RegPwm08 = 0x26  # PWM for channel 08
    RegPwm09 = 0x2A  # PWM for channel 09
    RegPwm10 = 0x2E  # PWM for channel 10
    RegPwm11 = 0x32  # PWM for channel 11
    RegPwm12 = 0x36  # PWM for channel 12
    RegPwm13 = 0x3A  # PWM for channel 13
    RegPwm14 = 0x3E  # PWM for channel 14
    RegPwm15 = 0x42  # PWM for channel 15
    RegALLLED = 0xFA    # PWm for all chanells
    RegPRE_SCALE = 0xFE # Prescale register
    RegTESTMODE = 0xFF  # Test mode register
    
    def __init__(self, i2c:I2C, address=0x61):
        self.__i2c = i2c
        self.__address = address

    def writeRegister(self, reg:int, value:int) -> None:
        # Write a value to a specific register
        self.__i2c.write(self.__address, bytes([reg, value]))
    
    def readRegister(self, reg:int) -> int:
        # Read a value from a specific register
        readbuffer = bytearray(1)
        self.__i2c.write_readinto(self.__address, bytes([reg]), readbuffer)
        return readbuffer[0]  # Return the read value

    def savePwm(self, value:int) -> tuple[int, int]:
        if value >= 4095:
            valueOn = 4096   # speciální hodnota pro trvalou 1
            valueOff = 0
        elif value <= 0:
            valueOn = 0
            valueOff = 4096   # speciální hodnota pro trvalou 0
        else:
            valueOn = 0
            valueOff = value
        return valueOn, valueOff
    
    def writePwmToHbridge(self, channel:int, value:int) -> None:
        # Write a PWM value to a specific channel and chanel+1
        # The value should be between -4095 and 4095 (12-bit resolution)
        # positive value for forward (channel+0), negative for backward (channel+1)
        # The channel should be between 0 and 14
        if value > 0:
            valueOn0, valueOff0 = self.savePwm(value)
            valueOn1, valueOff1 = self.savePwm(0)
        else:
            valueOn0, valueOff0 = self.savePwm(0)
            valueOn1, valueOff1 = self.savePwm(-value)
        # print('value:', hex(valueOn0), hex(valueOff0), hex(valueOn1), hex(valueOff1))
        self.__i2c.write(self.__address, bytes(
            [
                channel * 4 + PCA9685.RegPwm00, 
                valueOn0 & 0xFF, valueOn0 >> 8, valueOff0 & 0xFF, valueOff0 >> 8,
                valueOn1 & 0xFF, valueOn1 >> 8, valueOff1 & 0xFF, valueOff1 >> 8,
            ]
        ))

pca9685 = PCA9685(i2c)

class Wheel:
    # Třída implementující motor
    def __init__(self, place:int, radius:float, tickPerCircle: int, calibrateFactors:CalibrateFactors) -> None:
        self.__place = place
        self.__encoder = Encoder(place, tickPerCircle, radius)
        self.__pwmRegulator = RegulatorP(p=12, timeout_ms=500)
        self.calibrateFactors = calibrateFactors
        self.__radius = radius
        self.__angularSpeed = 0.0
        self.__pwm = 0
        if place == DirectionEnum.RIGHT:
            self.__pwmReg_Back = PCA9633.RegPWM0
            self.__pwmReg_Forw = PCA9633.RegPWM1
        elif place == DirectionEnum.LEFT:
            self.__pwmReg_Back = PCA9633.RegPWM2
            self.__pwmReg_Forw = PCA9633.RegPWM3
        else:
            raise ValueError("Wheel: Invalid place")

    def isStopped(self) -> bool:
        # je detekováno, že (asi) stojíme?
        return self.__encoder.isStopped()

    def stop(self) -> None:
        # bezpečnostní odstavení motorů
        self.__angularSpeed = 0.0
        self.ridePwm(0)

    def getMinimumForwardSpeed(self) -> float:
        # dej mi minimální doprednou rychlost kola robota z kalibrace kol
        return self.calibrateFactors.minimumAngularSpeed * self.__radius

    def __calculateAngularSpeed(self, forwardSpeed) -> float:
        # spočti uhlovou rychlost kola v rad/s z dopredne rychlosti v m/s
        return forwardSpeed / self.__radius

    def rideSpeed(self, forwardSpeed:float) -> None:
        # jeď touto dopřednou rychlostí kola
        self.__angularSpeed = self.__calculateAngularSpeed(forwardSpeed)
        pwm = self.calibrateFactors.calculatePwm(self.__angularSpeed)
        self.ridePwm(pwm)

    def __checkMinimumPwm(self, pwm:int) -> int:
        minPwm = self.calibrateFactors.getMinimumPwm(self.isStopped())
        if abs(pwm) < minPwm:
            if pwm < 0:
                minPwm *= -1
            # print('minimumPwm', minPwm)
            return minPwm
        return pwm

    def __checkMaximumPwm(self, pwm:int) -> int:
        if pwm > 255:
            pwm = 255
        if pwm < -255:
            pwm = -255
        return pwm

    def ridePwm(self, pwm:int) -> None:
        if pwm != 0.0:   # pokud máme NEnulovou rychlost, tak vyřeš minimální a maximální hodnoty pwm
            pwm = self.__checkMinimumPwm(pwm)
            pwm = self.__checkMaximumPwm(pwm)
        # sem by se uz mala dostat správná (omezena) hodnota pwm
        self.__pwm = pwm
        self.__writePwm(pwm)

    def __writePwm(self, pwm:int) -> None:
        # funkce pro nastavení pwm na motoru (bez omezeni velikosti pwm)
        if pwm >= 0:
            pca9633.clearRegister_writeRegister(self.__pwmReg_Back, self.__pwmReg_Forw, pwm)
        else:
            pca9633.clearRegister_writeRegister(self.__pwmReg_Forw, self.__pwmReg_Back, -pwm)

    def __changePwm(self, changeValue:float) -> None:
        # změn pwm o tuto hodnotu
        # if self.__place == DirectionEnum.LEFT:
        #     print(self.__pwm,'+',changeValue,'=',round(self.__pwm + changeValue))
        self.ridePwm(round(self.__pwm + changeValue))

    def getSpeed(self, unit:int, count=5, offset=0) -> float:
        # dej mi zmerenou rychlost kola v teto jednotce
        return self.__encoder.getSpeed(unit, count, offset)

    def regulatePwm(self, startRegulate:bool=False, stopRegulate:bool=False) -> None:
        if startRegulate:
            if not self.__pwmRegulator.isStarted():
                self.__pwmRegulator.startTimer()
        if stopRegulate:
            if self.__pwmRegulator.isStarted():
                self.__pwmRegulator.stopTimer()
        # reguluj pwm podle zmerene rychlosti kola
        time_ms = ticks_ms()
        if self.__pwmRegulator.isTimeout(time_ms):
            measuredAngularSpeed = self.__encoder.getSpeed(MeasureUnit.RadianPerSecond)
            changePwm = self.__pwmRegulator.getActionIntervention(
                time_ms, self.__angularSpeed, measuredAngularSpeed
            )
            self.__changePwm(changePwm)

    def update(self) -> None:
        self.__encoder.update(isForward = self.__pwm >= 0)
        self.regulatePwm()

    def getOdometryTicks(self) -> int:
        return self.__encoder.getOdometryTicks()
    
    def printCalibrateFactors(self) -> None:
        print(self.calibrateFactors)

class CalibratedWheel(Wheel):

    def cal_init(self) -> None:
        self.__minSpeed = 0
        self.__minPwmStop = -1
        self.__minPwmMotion = -1

    def cal_updateMinimumStop(self, speed:float, pwm:int) -> None:
        if speed == 0.0:
            self.__minPwmStop = None
            self.__minSpeed = 0.0
        elif self.__minPwmStop is None:
            self.__minPwmStop = abs(pwm)
            self.__minSpeed = abs(speed)

    def cal_updateMinimumMotion(self, speed:float, pwm:int) -> None:
        if speed != 0.0:
            self.__minPwmMotion = abs(pwm)

    def cal_getMinimumPwmStop(self) -> int:
        return self.__minPwmStop

    def cal_calculateFactors(self, speed:float, pwm:int) -> None:
        speed = abs(speed)
        print("cal_calculateFactors: speed", speed, "pwm", pwm, "minSpeed", self.__minSpeed, "minPwmStop", self.__minPwmStop, "minPwmMotion", self.__minPwmMotion)
        speedDiff = speed - self.__minSpeed
        if speedDiff == 0:
            # pokud je rozdil rychlosti nula, tak se nedaji kalibracni faktory spocitat
            print("Error: cal_calculateFactors: speedDiff == 0!")
            Display.drive_mode('E')
            Display.positionEmpty()
            return
        if self.__minPwmStop is None:
            # pokud je minPwmStop None, tak se nedaji kalibracni faktory spocitat
            print("Error: cal_calculateFactors: minPwmStop == None!")
            System.display_drive_mode('E')
            System.display_positionEmpty()
            return
        pwmDiff = pwm - self.__minPwmStop
        a = pwmDiff / speedDiff
        b = pwm - a * speed
        self.calibrateFactors = CalibrateFactors(self.__minSpeed, self.__minPwmStop, self.__minPwmMotion, a, b)        
        self.printCalibrateFactors()

class Wheels:
    # Třída implementující motory diferenciálního podvozku
    def __init__(self, halfWheelbase: float, wheelRadius: float, ticksPerCircle: int, calibrates: list[CalibrateFactors]) -> None:
        self.__halfWheelbase = halfWheelbase
        self.initMotorDriver()
        self.__wheels = [
            CalibratedWheel(direction, wheelRadius, ticksPerCircle, calibrate)
            for direction, calibrate in zip([DirectionEnum.LEFT, DirectionEnum.RIGHT], calibrates)
        ]

    def rideSpeed(self, forward:float, angular:float) -> None:
        # kinematika diferencionalniho podvozku
        self.__wheels[0].rideSpeed(forward - self.__halfWheelbase * angular)
        self.__wheels[1].rideSpeed(forward + self.__halfWheelbase * angular)

    def initMotorDriver(self) -> None:
        # inicializuj pwm driver pro motor
        pca9633.writeRegister(PCA9633.RegMODE1, 0x00)   # vypni sleep a všechny SW adresy
        pca9633.writeRegister(PCA9633.RegLEDOUT, 0xAA)  # nastav všechny 4 výstupy ovládané přes PWMx

    def stop(self) -> None:
        for wheel in self.__wheels:
            wheel.stop( )

    def emergencyShutdown(self) -> None:
        # Bezpečné odstavení všech motorů
        exceptions = []
        for wheel in self.__wheels:
            try:
                wheel.stop()
            except BaseException as e:
                exceptions.append(e)
        if exceptions:
            # TODO: Zde by asi mělo být odpojení motorů od napájení (zatím to neumíme)
            raise RuntimeError("Chyba při odstavení motorů", exceptions)

    def getMinimumSpeed(self) -> float:
        # Dej mi minimální rychlost robota ze všech kalibračních hodnot motorů
        return max(wheel.getMinimumForwardSpeed() for wheel in self.__wheels)
    
    def getSpeed(self, unit: int) -> list[float]:
        return [wheel.getSpeed(unit) for wheel in self.__wheels]

    def getOdometryTicks(self) -> list[int]:
        return [wheel.getOdometryTicks() for wheel in self.__wheels]

    def stopRegulatePwm(self) -> None:
        for wheel in self.__wheels:
            wheel.regulatePwm(stopRegulate=True)

    def startRegulatePwm(self) -> None:
        for wheel in self.__wheels:
            wheel.regulatePwm(startRegulate=True)

    def update(self) -> None:
        for wheel in self.__wheels:
            wheel.update()
    
    def printCalibrateFactors(self) -> None:
        for wheel in self.__wheels:
            wheel.printCalibrateFactors()

class CalibratedWheels(Wheels):
    cal_debug = False

    def __cal_init(self) -> None:
        for wheel in self.__wheels:
            wheel.cal_init()

    def __cal_writePwm(self, pwm: list[int]) -> None:
        for wheel, pwm_value in zip(self.__wheels, pwm):
            # print(pwm_value)
            wheel.__writePwm(pwm_value)
    
    def __cal_updateMinimumStop(self, speeds:list[float], pwm:int) -> None:
        for wheel, speed_value in zip(self.__wheels, speeds):
            wheel.cal_updateMinimumStop(speed_value, pwm)

    def __cal_updateMinimumMotin(self, speeds:list[float], pwm:int) -> None:
        for wheel, speed_value in zip(self.__wheels, speeds):
            wheel.cal_updateMinimumMotion(speed_value, pwm)

    def __cal_calculateFactors(self, speeds:list[float], pwm:list[int]) -> None:
        for wheel, speed_value, pwm_value in zip(self.__wheels, speeds, pwm):
            wheel.cal_calculateFactors(speed_value, pwm_value)

    def __cal_writePwm_getMeasuredSpeed(self, pwm: int) -> list[float]:
        System.display_number(abs(pwm))
        self.__cal_writePwm([pwm, -pwm])
        # pockej az se zmeri rychlost po zmene pwm
        for wait in range(500):
            self.update()
            System.updatePixels()
        # vrat zmerene rychlosti jednotlivych kol
        speeds = self.getSpeed(MeasureUnit.RadianPerSecond)
        if self.cal_debug:
            print("pwm", pwm, "speeds", speeds)
        return speeds

    def __cal_getMinimumPwmStop(self) -> int:
        values = [wheel.cal_getMinimumPwmStop() for wheel in self.__wheels if wheel.cal_getMinimumPwmStop() is not None]       
        if values:  # Pokud jsou platné hodnoty, vrátíme minimum
            return min(values)                
        return -1

    def __cal_speedIsNotZero(self, speeds:list[float]) -> bool:
        # zjisti zda se vsechna kola točí
        for speed in speeds:
            if speed == 0.0:
                return False
        return True

    def __cal_speedIsZero(self, speeds:list[float]) -> bool:
        # zjisti zda se vsechna kola stoji
        for speed in speeds:
            if speed != 0.0:
                return False
        return True

    def calibration(self, pwmFrom:int, pwmTo:int, pwmSkip:int) -> None:
        if self.cal_debug:
            print("calibration: pwmFrom", pwmFrom, "pwmTo", pwmTo, "pwmSkip", pwmSkip)
        self.__cal_init()
        self.stopRegulatePwm()
        # stoupame s pwm - začneme s počátačním pwm
        pwm = pwmFrom
        while True:
            speeds = self.__cal_writePwm_getMeasuredSpeed(pwm)
            self.__cal_updateMinimumStop(speeds, pwm)
            if pwm == pwmTo:
                # pokud jsme s pwm na konci, tak tento krok končíme
                break

            # budeme opakovat zvyšování pwm dokud se všechna kola nezačnou točit
            if (self.__cal_speedIsNotZero(speeds)):
                pwm = pwmTo                    # pokud se kola točí skočíme s pwm nakonec
            else:
                pwm += pwmSkip

        self.stop()
        speedsMax = speeds
        sleep(50)
        # klesame s pwm - začneme tam, kde se motory rozjeli
        pwm = self.__cal_getMinimumPwmStop()
        if self.cal_debug:
            print("minPwm", pwm, "speedsMax", speedsMax)
        while pwm >= 0:
            speeds = self.__cal_writePwm_getMeasuredSpeed(-pwm)
            self.__cal_updateMinimumMotin(speeds, pwm)
            # budeme opakovat snižování pwm dokud se kola budou pohybovat
            if (self.__cal_speedIsZero(speeds)):
                break
            else:
                pwm -= pwmSkip
        self.stop()
        self.__cal_calculateFactors(speedsMax, [pwmTo, pwmTo])

class MotionControl:
    # Třída implementující kinematiku robota
    def __init__(self, wheelbase:float, wheelDiameter:float, ticksPerCircle:int, velocity:Velocity, calibrateFactors:list[CalibrateFactors]) -> None:
        self.__wheelRadius = wheelDiameter / 2
        self.__wheels = CalibratedWheels(wheelbase / 2, self.__wheelRadius, ticksPerCircle, calibrateFactors)
        self.velocity = velocity
        self.__newVelocity(self.velocity.forward, self.velocity.angular)
        self.odometry = Odometry()
        self.odometry.odometry_init(wheelbase, self.__wheelRadius, ticksPerCircle)

    def stop(self) -> None:
        self.__newVelocity(0, 0)

    def emergencyShutdown(self) -> None:
        # bezpečnostní odstavení motorů robota
        try:
            self.stop()
        except BaseException as e:
            self.__wheels.emergencyShutdown()
            raise e

    def stopRegulatePwm(self) -> None:
        self.__wheels.stopRegulatePwm()

    def calibration(self, pwmFrom, pwmTo, pwmSkip) -> None:
        self.__wheels.calibration(pwmFrom, pwmTo, pwmSkip)

    def getMinimumSpeed(self) -> float:
        # dej mi minimální rychlost robota z kalibračních hodnot
        return self.__wheels.getMinimumSpeed()

    def newVelocity(self, forward:float=0.0, angular:float=0.0):
        if (self.velocity.forward != forward) or (self.velocity.angular != angular):
            self.__newVelocity(forward, angular)

    def __newVelocity(self, forward, angular):
        # nastav nové požadované rychlosti pohybu robota a přepočti je podle kinematiky do jednotlivých motorů
        self.velocity.forward = forward
        self.velocity.angular = angular
        self.__wheels.rideSpeed(forward, angular)   

    def update(self) -> None:
        self.__wheels.update()
        self.odometry_update()

    def odometry_update(self) -> None:
        time_ms = ticks_ms()
        if self.odometry.isTimeout(time_ms):
            # už je čas znovu spočítat odometrii
            self.odometry_recalculate(time_ms)
    
    def odometry_recalculate(self, time_ms:int=None) -> None:
        # spočítej pozici odometrie (ze změny tiků levého a pravého kola)
        self.odometry.odometry_calculate(self.__wheels.getOdometryTicks())
        self.odometry.odometry_startTimer(time_ms)

    def odometry_reinit(self) -> None:
        # vycti zbytky tiků po predchozim pohybu a nastartuj časovač výpočtu odometrie
        self.odometry_recalculate()
        # nastav pozici na init hodnoty
        self.odometry.odometry_reinit()
