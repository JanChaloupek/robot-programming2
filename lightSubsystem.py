from HardwarePlatform import pin0
from directions import DirectionEnum
from neopixel import NeoPixel
from velocity import Velocity
from timer import Timer

class IndicatorStateEnum:
    SPACE = 1
    LIGHT = 2

class BeamsEnum:
    DippedBeams = 1
    HighBeams = 2

class IndicatorState(Timer):

    def __init__(self) -> None:
        super().__init__(timeout_ms=400)
        self.reset() 

    def set(self, value:int) -> None:
        self.value: int = value
        self.startTimer()

    def reset(self) -> None:
        self.set(None)

    def isDifferent(self, other:int) -> bool:
        # je hodnota stavu rozdílná od předané?
        return self.value != other

    def __change_Light_Space(self) -> None:
        # změn stav blinkru
        self.set(IndicatorStateEnum.SPACE if self.value == IndicatorStateEnum.LIGHT else IndicatorStateEnum.LIGHT)

    def changeState(self) -> None:
        if self.value is not None:
            # jestli blinkr uz blikal, pockej na timeout a zmen stav
            if self.isTimeout():
                self.__change_Light_Space()
        else:
            # jeste neblikal, tak zapni svetlo blinkru
            self.set(IndicatorStateEnum.LIGHT)

class Lights(Timer):
    # Třída implementující ledky jako světla robota (používá knihovnu NeoPixel)
    color_led_off = (0, 0, 0)
    color_led_orange = (100, 35, 0)
    color_led_white = (60, 60, 60)
    color_led_white_hi = (255, 255, 255)
    color_led_red = (60, 0, 0)
    color_led_red_br = (255, 0, 0)

    def __init__(self) -> None:
        super().__init__(timeout_ms=100)
        self.__neopixels = NeoPixel(pin0, 8)

    def setColorToOneLed(self, ledNo:int, color:int) -> None:
        # nastav barvu pro jednu led-ku
        self.__neopixels[ledNo] = color

    def setColor(self, ledList:int, color:int) -> None:
        # nastav barvu pro seznam led-ek
        for ledNo in ledList:
            self.setColorToOneLed(ledNo, color)

    def showColor(self) -> None:
        # zapiš nastavené barvy do led-ek
        self.__neopixels.write()

class LightsControl:
    # Třída implementující jednotlivá světla

    # (blinkry, zpátečku, brzdy, potkávací a dálková světla)
    ind_all = (1, 2, 4, 7)
    ind_left = (1, 4)
    ind_right = (2, 7)
    head_lights = (0, 3)
    back_lights = (5, 6)
    inside_light = (0, 3, 5, 6)
    reverse_lights = (5,)

    def __init__(self, velocity:Velocity) -> None:
        self.__lights = Lights()
        self.__indicatorState = IndicatorState()
        self.__oldForward = 0.0
        self.__velocity = velocity
        self.main = None
        self.indicator = None
        self.warning = False
        self.setReverseFromVelocity()
        self.__isBrake = False
        self.__brakeTimer = Timer()

    def indicatorsIsBlink(self) -> bool:
        # maji blikat nejake blinkry?
        return self.indicator is not None or self.warning

    def leftIndicatorIsBlink(self) -> bool:
        # maji blikat leve blinkry?
        return self.indicator == DirectionEnum.LEFT or self.warning

    def rightIndicatorIsBlink(self) -> bool:
        # maji blikat prave blinkry?
        return self.indicator == DirectionEnum.RIGHT or self.warning

    def setReverseFromVelocity(self) -> None:
        # spočti zapnutí couvacího světla z rychlosti robota
        self.__isReverse = self.__velocity.forward < 0.0

    def setBrakeFromVelocity(self) -> None:
        # spočti brzdové světlo z požadované dopředné rychlosti robota
        if self.__velocity.forward == 0.0 and self.__oldForward != 0.0:
            # pokud mame zastavit ale predtim jsme jeli => brzdime
            self.__isBrake = True
            self.__brakeTimer.startTimer()
        self.__oldForward = self.__velocity.forward

    def isBrake(self) -> bool:
        # má svítit brzdové světlo?
        if self.__isBrake:
            if not self.__brakeTimer.isTimeout(timeout_ms=600):
                return True
            self.__isBrake = False
        return False

    def setColorIndicator(self) -> None:
        # nastav stavy blinkrovych svetel
        if self.__indicatorState.value == IndicatorStateEnum.LIGHT:
            if self.leftIndicatorIsBlink():
                self.__lights.setColor(self.ind_left, Lights.color_led_orange)
            if self.rightIndicatorIsBlink():
                self.__lights.setColor(self.ind_right, Lights.color_led_orange)
        else:
            self.__lights.setColor(self.ind_all, Lights.color_led_off)

    def setColorOtherLights(self) -> None:
        # nastav barvy prednich a zadnich svetel (ne blinkru)
        headColor = Lights.color_led_off
        backColor = Lights.color_led_off
        if self.main == BeamsEnum.DippedBeams:
            headColor = Lights.color_led_white
            backColor = Lights.color_led_red
        if self.main == BeamsEnum.HighBeams:
            headColor = Lights.color_led_white_hi
            backColor = Lights.color_led_red

        if self.isBrake():
            backColor = Lights.color_led_red_br

        self.__lights.setColor(self.head_lights, headColor)
        self.__lights.setColor(self.back_lights, backColor)
        
        if self.__isReverse:
            self.__lights.setColor(self.reverse_lights, Lights.color_led_white)

    def updateIndicatorState(self) -> None:
        # aktualizace stavu blinkru
        if self.indicatorsIsBlink():
            # blinkry mají blikat, tak měn stav = blikej
            self.__indicatorState.changeState()
        else:
            # blinkry mají být zhasnuté
            self.__indicatorState.reset()

    def update(self) -> None:
        self.setReverseFromVelocity()
        self.setBrakeFromVelocity()

        backupState = self.__indicatorState.value
        self.updateIndicatorState()
        if self.__indicatorState.isDifferent(backupState) or self.__lights.isTimeout():
            self.setColorIndicator()
            self.setColorOtherLights()
            self.__lights.showColor()
            self.__lights.startTimer()

