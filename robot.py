from HardwarePlatform import ticks_diff, ticks_ms, i2c, led, ROBOT_DIAMETER, WHEEL_DIAMETER, TICKS_PER_CIRCLE
from calibrateFactors import CalibrateFactors
from lightSubsystem import LightsControl
from motionSubsystem import MotionControl
from regulator import RegulatorP
from directions import DirectionEnum
from tempomat import Tempomat
from velocity import Velocity
from senzors import Senzors
from position import Point
from sonar import Sonar
from timer import Timer

class Robot:
    # Základní třída s robotem
    def __init__(self, robotDiameter:float, wheelDiameter:float, ticksPerCircle:int, calibrateFactors:list[CalibrateFactors]) -> None:
        velocity = Velocity()
        i2c.init(freq=400_000)
        # senzory (vcetne ultrazvuku)
        self.__senzors = Senzors()
        self.__sonar = Sonar()
        # ovladani svetel
        self.lightsControl = LightsControl(velocity)
        # ovladani pohybu
        self.motionControl = MotionControl(robotDiameter, wheelDiameter, ticksPerCircle, velocity, calibrateFactors)
        self.motionControl.newVelocity(0, 0)
        # objekt tempomatu (funguje az po nastaveni vzdalenosti kteou ma udrzovat)
        self.tempomat = Tempomat()
        # cas za který prejedeme krizovatku (abychom cca byli stredem otaceni nad krizovatkou)
        self.__exitCrossRoadsTimer = Timer()
        # cas po ktery nebudeme verit ze jsem spravne natoceni (mohli bychom "chytit" caru pred nami misto te na kterou chceme zatocit)
        self.__turnErrorTimer = Timer()
        # natoceni a sledovani nasledujiciho bodu na mape (sledovani mrkve)
        self.__regulatorFollow = RegulatorP(p=2, timeout_ms=300)
        self.__regulatorTurn = RegulatorP(p=1, timeout_ms=100)
        # pro sledovani cary
        self.__lastVelocityInFollowingLine = Velocity()
        self.__maxSpeed = 0.3
        self.__minSpeed = self.motionControl.getMinimumSpeed()
        self.__timeTurn = 0
        # casovac pro signalizaci zivota (blikani led)
        self.__ledTimer = Timer()

    def getSenzors(self) -> Senzors:
        return self.__senzors

    def stop(self) -> None:
        self.motionControl.stop()

    def emergencyShutdown(self) -> None:
        # bezpečnostní zastavení robota (něco špatného se stalo)
        self.motionControl.emergencyShutdown()

    def getObstacleDistance(self) -> None:
        # vrať poslední známou vzdálenost od překážky
        return self.__sonar.lastDistance

    def __testBumber(self) -> None:
        # pokud mame prekazku pred narazniky tak zastav
        if self.__senzors.getAnySenzor(Senzors.ObstaleLeft | Senzors.ObstaleRight):
            self.motionControl.newVelocity(0, 0)

    def speedLimitation(self, speed) -> float:
        # omezení maximální a minimální dopředné rychlosti
        if speed >= 0:
            sign = 1
        else:
            sign = -1
        absSpeed = abs(speed)
        if absSpeed > self.__maxSpeed:
            absSpeed = self.__maxSpeed
        elif absSpeed < self.__minSpeed:
            absSpeed = self.__minSpeed
        return sign * absSpeed
       
    def tempomat_updateSpeed(self) -> None:
        # reguluj dopředou rychlost podle vzdálenosti od překážky
        speed = self.tempomat.calculateSpeed(self.getObstacleDistance)
        if speed is not None:
            speed = self.speedLimitation(speed)
            self.motionControl.newVelocity(speed, 0)

    def rideLine(self, baseForward=0.2, baseAngular=0.3, back:bool=False) -> None:
        # reguluj zatáčení podle sledovače čáry
        time = ticks_ms()
        if self.__regulatorTurn.isTimeout(time):

            if self.tempomat.isActivate():                                            # je aktivovany tempomat?
                distance = self.getObstacleDistance()
                tempomatSpeed = self.tempomat.getSpeedFromDistance(time, distance)    # spocti rychlost ze vzdalenosti od prekazky
                # na dalnici nesmime couvat -> takže připustíme jen kladné rychlosti
                tempomatSpeed = max(0, tempomatSpeed)
                if tempomatSpeed < baseForward:
                    baseForward = tempomatSpeed                                    # pokud tempomat omezil rychlost, tak pojedeme pomaleji

            lineDirection = self.__senzors.getLineDirection()

            if baseForward == 0.0:
                # pokud tempomat chce abychom zastavili, tak zastavime (nebudeme ani zatacet - neni duvod se tocit na miste)
                forward = 0.0
                angular = 0.0
            elif lineDirection is None:
                # pokud jsme mimo caru tak jed stejne jak mame zapamatovane z minula
                forward = self.__lastVelocityInFollowingLine.forward
                angular = self.__lastVelocityInFollowingLine.angular
                self.__timeTurn += 1
            elif lineDirection == 0:
                # vidim caru pod středním(i) senzor(em/y) -> jedeme rovne plnou rychlosti
                forward = baseForward
                angular = 0.0
                self.__timeTurn = 0
            else:
                self.__timeTurn += 1
                # vidim caru pod některým krajním senzorem, zpomal a zatoc (podle lineDirection)
                koef = self.__getTurnCoef(lineDirection)
                forward = baseForward / abs(koef)
                angular = baseAngular * koef

            self.__lastVelocityInFollowingLine.angular = angular
            self.__lastVelocityInFollowingLine.forward = forward
            # pokud se požadovaná úhlová rychlost změnila, požádáme ovladač motorů o změnu rychlosti
            if back:
                forward *= -1
            self.motionControl.newVelocity(forward, angular)

    def __getTurnCoef(self, lineDirection:int) -> float:
        # vrat nasobici koeficient pro zataceni
        timeTurnCoef = 0.0
        if lineDirection < 0:
            timeTurnCoef *= -1
        return lineDirection + self.__timeTurn * timeTurnCoef

    def getSituationLine(self) -> int:
        # vrat situaci sledovani cary
        return self.__senzors.getSituationLine()

    def update(self) -> None:
        # aktualizuj subsystemy
        self.motionControl.update()
        self.lightsControl.update()
        self.__senzors.update()
        self.__sonar.update()
        self.__testBumber()
        # signalizuj ze program zije
        if self.__ledTimer.isTimeout(timeout_ms=150):
            self.__ledTimer.startTimer()
            led.toggle()

    def exitCrossRoads_start(self) -> None:
        self.__exitCrossRoadsTimer.startTimer()

    def exitCrossRoads(self, direction:int, forward:float=0.1, angular:float=0.1) -> bool:
        # pote co jsme dojeli na krizovatku, ji opoustime (zatacej a popojizdej "spravnym" smerem)
        if direction == DirectionEnum.FORWARD:
            # pojedeme kousek dopredu a nebudeme zatacet
            angular = 0.0
        elif direction == DirectionEnum.BACKWARD:
            # pojedeme kousek dozadu a nebudeme zatacet
            forward *= -1
            angular = 0.0
        elif direction == DirectionEnum.LEFT:
            # pojedeme kousek dopredu a budeme zatacet vlevo (kladna uhlova rychlost)
            pass
        elif direction == DirectionEnum.RIGHT:
            # pojedeme kousek dopredu a budeme zatacet vpravo (zaporna uhlova rychlost)
            angular *= -1
        else:
            # nesmyslny smer -> pro jistotu zastav at do neceho nevrazis (on to nekdo spravi)
            forward = 0.0
            angular = 0.0
        self.motionControl.newVelocity(forward, angular)

        if not self.__exitCrossRoadsTimer.isTimeout(timeout_ms=300):
            # jeste neuplynul cas na opusteni krizovatky
            return False
        # uz to trva dost dlouho (meli bychom být za křižovatkou)
        return True

    def turningToLine_start(self) -> None:
        self.__turnErrorTimer.startTimer()

    def turningToLine(self, direction:int, angularSpeed:float) -> bool:
        # pote co jsme dojeli nad krizovatku, otacej se spravnym smerem        
        if direction==DirectionEnum.LEFT:
            angular = angularSpeed
        elif direction==DirectionEnum.RIGHT:
            angular = -angularSpeed
        else:
            angular = 0.0   # pokud je spatný směr neotáčej se nikam
        self.motionControl.newVelocity(0.0, angular)

        # jsme prostředními senzory nad čářou (stačí alespoň jeden ze středních)?
        if self.__senzors.getAnySenzor(self.__senzors.getMiddleSenzorsAddr()):
            # muzeme skoncit otaceni jen kdyz trva alespon nejakou dobu (prevence chyceni cary pred sebou)
            if self.__turnErrorTimer.isTimeout(timeout_ms=1_000):
                return True
        # porad nejsme natoceni spravne
        return False

    def follow(self, point:Point, forward:bool) -> tuple[bool, bool]:
        time = ticks_ms()
        if forward:
            run = self.__regulatorFollow.isTime(time)
        else:
            run = self.__regulatorTurn.isTime(time)
        if run:
#            print("robot.follow - isTimeout")
            self.motionControl.odometry_recalculate(time)
            distance, deltaTheta = self.motionControl.odometry.calculate_directionToPoint(point)
            angular = self.__regulatorTurn.getActionIntervention(time, 0, -deltaTheta)
            if angular > 0.5:
                angular = 0.5
            if angular < -0.5:
                angular = -0.5
            
            if forward:
                speed = self.__regulatorFollow.getActionIntervention(time, 0, -distance)
                if speed > 0.2:
                    # pokud je pozadavek na rychlost moc velky omezime ho
                    speed = 0.2
            else:
                # pokud se tocime do spravneho smeru nepojedeme dopredu
                speed = 0

#            print("follow (distance, deltaTheta, speed, angular):", distance, deltaTheta, speed, angular)
            self.motionControl.newVelocity(speed, angular)
            if forward:
                return abs(deltaTheta) > 0.2, abs(distance) <= 0.03
            else:
                return abs(deltaTheta) <= 0.05, False
        return False, False


def createRobotJoyCar() -> Robot:
    # inicializace robota
    leftCalibrate = CalibrateFactors(0.5, 130, 80, 11.692, 28.643)
    rightCalibrate = CalibrateFactors(0.5, 130, 80, 12.259, 26.332)
    return Robot(ROBOT_DIAMETER, WHEEL_DIAMETER, TICKS_PER_CIRCLE, [leftCalibrate, rightCalibrate])
