from HardwarePlatform import i2c, I2C_ADDR_MOTION, ticks_ms, sleep, ticks_diff, display
from calibrateFactors import CalibrateFactors
from speedMeasure import Encoder, MeasureUnit
from regulator import RegulatorP
from directions import DirectionEnum
from velocity import Velocity
from position import Odometry

from HardwarePlatform import I2C

class PCA9633:
    Reg_MinAddr = 0x00  # Minimum address register 
    Reg_MaxAddr = 0x0C  # Maximum address register

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

pca9633 = PCA9633(i2c)

class Wheel:
    # Třída implementující motor
    def __init__(self, place:int, radius:float, tickPerCircle: int, calibrateFactors:CalibrateFactors) -> None:
        self.__place = place
        self.__encoder = Encoder(place, tickPerCircle, radius)
        self.__pwmRegulator = RegulatorP(p=12, timeout_ms=500)
        self.__calibrateFactors = calibrateFactors
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
        return self.__calibrateFactors.minimumAngularSpeed * self.__radius

    def __calculateAngularSpeed(self, forwardSpeed) -> float:
        # spočti uhlovou rychlost kola v rad/s z dopredne rychlosti v m/s
        return forwardSpeed / self.__radius

    def rideSpeed(self, forwardSpeed:float) -> None:
        # jeď touto dopřednou rychlostí kola
        self.__angularSpeed = self.__calculateAngularSpeed(forwardSpeed)
        pwm = self.__calibrateFactors.calculatePwm(self.__angularSpeed)
        self.ridePwm(pwm)

    def __checkMinimumPwm(self, pwm:int) -> int:
        minPwm = self.__calibrateFactors.getMinimumPwm(self.isStopped())
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
        if self.__pwmRegulator.isTime(time_ms):
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

    def calibrate_init(self) -> None:
        self.__minSpeed = 0
        self.__minPwmStop = -1
        self.__minPwmMotion = -1

    def calibrate_updateMinimumStop(self, speed:float, pwm:int) -> None:
        if speed == 0.0:
            self.__minPwmStop = None
            self.__minSpeed = 0.0
        elif self.__minPwmStop is None:
            self.__minPwmStop = abs(pwm)
            self.__minSpeed = abs(speed)
        
    def calibrate_updateMinimumMotion(self, speed:float, pwm:int) -> None:
        if speed != 0.0:
            self.__minPwmMotion = abs(pwm)

    def calibrate_getMinimumPwmStop(self) -> int:
        return self.__minPwmStop

    def createCalibrateFactors(self, speed:float, pwm:int):
        speed = abs(speed)
        speedDiff = speed - self.__minSpeed
        pwmDiff = pwm - self.__minPwmStop
        a = pwmDiff / speedDiff
        b = pwm - a * speed
        self.__calibrateFactors = CalibrateFactors(self.__minSpeed, self.__minPwmStop, self.__minPwmMotion, a, b)        


class Wheels:
    # Třída implementující motory diferenciálního podvozku
    def __init__(self, halfWheelbase:float, wheelRadius:float, ticksPerCircle:int, calibrates:list[CalibrateFactors]) -> None:
        self.__wheelLeft  = Wheel(DirectionEnum.LEFT , wheelRadius, ticksPerCircle, calibrates[0])
        self.__wheelRight = Wheel(DirectionEnum.RIGHT, wheelRadius, ticksPerCircle, calibrates[1])
        self.__halfWheelbase = halfWheelbase
        self.initMotorDriver()

    def initMotorDriver(self) -> None:
        # inicializuj pwm driver pro motor
        pca9633.writeRegister(PCA9633.RegMODE1, 0x00)   # vypni sleep a všechny SW adresy
        pca9633.writeRegister(PCA9633.RegLEDOUT, 0xAA)  # nastav všechny 4 výstupy ovládané přes PWMx

    def stop(self) -> None:
        self.__wheelLeft.stop()
        self.__wheelRight.stop()

    def emergencyShutdown(self) -> None:
        # bezpečnostní odstavení motorů robota
        ex = None
        try:
            self.__wheelLeft.stop()
        except BaseException as e:
            ex = e
        try:
            self.__wheelRight.stop()
        except BaseException as e:
            ex = e
        if ex is not None:
            #TODO: zde by asi mělo být odpojení motorů od napájení (zatím to neumíme)
            raise ex

    def getMinimumSpeed(self) -> float:
        # dej mi minimální rychlost robota z kalibračních hodnot
        minimumLeft = self.__wheelLeft.getMinimumForwardSpeed()
        minimumRight = self.__wheelRight.getMinimumForwardSpeed()
        return max(minimumLeft, minimumRight)
    
    def getSpeed(self, unit: int) -> list[float]:
        return [
            self.__wheelLeft.getSpeed(unit),
            self.__wheelRight.getSpeed(unit),
        ]

    def getOdometryTicks(self) -> list[int]:
        return [
            self.__wheelLeft.getOdometryTicks(),
            self.__wheelRight.getOdometryTicks(),
        ]
        
    def stopRegulatePwm(self) -> None:
        self.__wheelLeft.regulatePwm(stopRegulate=True)
        self.__wheelRight.regulatePwm(stopRegulate=True)

    def startRegulatePwm(self) -> None:
        self.__wheelLeft.regulatePwm(startRegulate=True)
        self.__wheelRight.regulatePwm(startRegulate=True)

    def update(self) -> None:
        self.__wheelLeft.update()
        self.__wheelRight.update()

    def rideSpeed(self, forward:float, angular:float) -> None:
        # kinematika diferencionalniho podvozku
        self.__wheelLeft.rideSpeed(forward - self.__halfWheelbase * angular)
        self.__wheelRight.rideSpeed(forward + self.__halfWheelbase * angular)

    def __calibrate_ridePwm(self, pwm:list[int]):
        self.__wheelLeft.ridePwm(pwm[0])
        self.__wheelRight.ridePwm(pwm[1])
    
    def __calibrate_updateMinimumStop(self, speeds:list[float], pwm:int) -> None:
        self.__wheelLeft.calibrate_updateMinimumStop(speeds[0], pwm)
        self.__wheelRight.calibrate_updateMinimumStop(speeds[1], pwm)

    def __calibrate_updateMinimumMotin(self, speeds:list[float], pwm:int) -> None:
        self.__wheelLeft.calibrate_updateMinimumMotion(speeds[0], pwm)
        self.__wheelRight.calibrate_updateMinimumMotion(speeds[1], pwm)

    def __createCalibrateFactors(self, speeds:list[float], pwm:list[int]) -> None:
        self.__wheelLeft.createCalibrateFactors(speeds[0], pwm[0])
        self.__wheelRight.createCalibrateFactors(speeds[1], pwm[1])

    def __printCalibrateFactors(self) -> None:
        print(str(self.__wheelLeft.__calibrateFactors))
        print(str(self.__wheelRight.__calibrateFactors))

    def __calibrate_writePwm_getMeasuredSpeed(self, pwm: int) -> list[float]:
        display.scroll(abs(pwm))
        self.__calibrate_ridePwm([pwm, -pwm])
        # pockej az se zmeri rychlost po zmene pwm
        for wait in range(600):
            self.update()
            sleep(1)
        # vrat zmerene rychlosti jednotlivych kol
        return self.getSpeed(MeasureUnit.RadianPerSecond)

    def calibration(self, pwmFrom:int, pwmTo:int, pwmSkip:int) -> None:
        self.stopRegulatePwm()
        self.__wheelLeft.calibrate_init()
        self.__wheelRight.calibrate_init()
        # stoupame s pwm - začneme s počátačním pwm
        pwm = pwmFrom
        while True:
            speeds = self.__calibrate_writePwm_getMeasuredSpeed(pwm)
            self.__calibrate_updateMinimumStop(speeds, pwm)
            if pwm == pwmTo:
                # pokud jsme s pwm na konci, tak tento krok končíme
                break

            # budeme opakovat zvyšování pwm dokud se všechna kola nezačnou točit
            if (speeds[0] != 0.0)and(speeds[1] != 0.0):
                # pokud se kola točí skočíme s pwm nakonec
                pwm = pwmTo
            else:
                pwm += pwmSkip

        self.stop()
        speedsMax = speeds
        sleep(50)
        # klesame s pwm - začneme tam, kde se motory rozjeli
        pwm = self.__calibrate_getMinimumPwmStop()
        while pwm >= 0:
            speeds = self.__calibrate_writePwm_getMeasuredSpeed(-pwm)
            self.__calibrate_updateMinimumMotin(speeds, pwm)
            print("pwm=", pwm, "lSpeed=", speeds[0], "rSpeed=", speeds[1])
            # budeme opakovat snižování pwm dokud se kola budou pohybovat
            if (speeds[0] == 0.0)and(speeds[1] == 0.0):
                break
            else:
                pwm -= pwmSkip
        self.stop()
        self.__createCalibrateFactors(speedsMax, [pwmTo, pwmTo])
        self.__printCalibrateFactors()


class MotionControl:
    # Třída implementující kinematiku robota
    def __init__(self, wheelbase:float, wheelDiameter:float, ticksPerCircle:int, velocity:Velocity, calibrateFactors:list[CalibrateFactors]) -> None:
        self.__wheelRadius = wheelDiameter / 2
        self.__wheels = Wheels(wheelbase / 2, self.__wheelRadius, ticksPerCircle, calibrateFactors)
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
