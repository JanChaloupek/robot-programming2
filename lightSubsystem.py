from HardwarePlatform import pin0
from directions import DirectionEnum
from neopixel import NeoPixel
from velocity import Velocity
from timer import Timer, Period

class BeamsEnum:
    DippedBeams = 1
    HighBeams = 2

class Indicator:
    # Třída implementující blinkr robota (nevykresluje, jen počítá stav)
    def __init__(self) -> None:
        self.direction = None
        self.warning = False
        self.__indicatorPeriod = Period(timeout_ms=400)
        self.indicatorLight = None

    def update(self) -> None:           
        # aktualizuj stav blinkru
        if self.isLeft() or self.isRight():                        # blinker má být zapnutý 
            if self.indicatorLight is None:                        # ale nebliká
                self.indicatorLight = True                         # tak zační blikat
                self.__indicatorPeriod.startTimer()
        else:                                                      # pokud má být vypnutý blinkr
            self.indicatorLight = None                             # vypni blinkr

        if self.indicatorLight is not None:                        # pokud blinkr bliká
            if self.__indicatorPeriod.isTime():                    # a uplynul čas
                self.indicatorLight = not self.indicatorLight      # tak přepni stav
            
    def isLeft(self) -> bool:
        # je zapnutý levý blinkr?
        return (self.direction == DirectionEnum.LEFT)or self.warning

    def isRight(self) -> bool:
        # je zapnutý pravý blinkr?
        return (self.direction == DirectionEnum.RIGHT)or self.warning    

class LightsControl:
    # Třída ovládající světla robota (používá knihovnu NeoPixel)
    color_led_off = (0, 0, 0)
    color_led_orange = (100, 35, 0)
    color_led_white = (60, 60, 60)
    color_led_white_hi = (255, 255, 255)
    color_led_red = (60, 0, 0)
    color_led_red_br = (255, 0, 0)

    # (blinkry, zpátečku, brzdy, potkávací a dálková světla)
    ind_all = (1, 2, 4, 7)
    ind_left = (1, 4)
    ind_right = (2, 7)
    head_lights = (0, 3)
    back_lights = (5, 6)
    inside_light = (0, 3, 5, 6)
    reverse_lights = (5,)

    def __init__(self, velocity:Velocity) -> None:
        self.main = None
        self.indicator = Indicator()
        self.__showPeriod = Period(timeout_ms=100)
        self.__neopixels = NeoPixel(pin0, 8)
        self.__oldForward = 0.0
        self.__velocity = velocity
        self.__oldForward = 0.0
        self.__brakeTimer = Timer(timeout_ms=600, startTimer=False)

    def __setBrakeFromVelocity(self) -> None:
        # spočti brzdové světlo z požadované dopředné rychlosti robota
        if self.__velocity.forward == 0.0 and self.__oldForward != 0.0:
            # pokud stojime ale predtim jsme jeli => brzdime
            self.__brakeTimer.startTimer()
        self.__oldForward = self.__velocity.forward

    def __isBrake(self) -> bool:
        # má svítit brzdové světlo?
        if self.__brakeTimer.isStarted():
            if not self.__brakeTimer.isTimeout(timeout_ms=600):
                return True
            self.__brakeTimer.stopTimer()
        return False

    def __isReverse(self) -> bool:
        return self.__velocity.forward < 0.0

    def __setColorIndicator(self) -> None:
        # nastav stavy blinkrovych svetel
        leftColor = LightsControl.color_led_off
        rightColor = LightsControl.color_led_off
        if self.indicator.indicatorLight == True:
            if self.indicator.isLeft():
                leftColor = LightsControl.color_led_orange
            if self.indicator.isRight():
                rightColor = LightsControl.color_led_orange
        self.__setColor(self.ind_left,  leftColor)
        self.__setColor(self.ind_right, rightColor)

    def __setColorOtherLights(self) -> None:
        # nastav barvy prednich a zadnich svetel (ne blinkru)
        headColor = LightsControl.color_led_off
        backColor = LightsControl.color_led_off
        if self.main == BeamsEnum.DippedBeams:
            headColor = LightsControl.color_led_white
            backColor = LightsControl.color_led_red
        if self.main == BeamsEnum.HighBeams:
            headColor = LightsControl.color_led_white_hi
            backColor = LightsControl.color_led_red

        if self.__isBrake():
            backColor = LightsControl.color_led_red_br

        self.__setColor(self.head_lights, headColor)
        self.__setColor(self.back_lights, backColor)
        
        if self.__isReverse():
            self.__setColor(self.reverse_lights, LightsControl.color_led_white)

    def update(self) -> None:
        self.indicator.update()
        if self.__showPeriod.isTime():
            self.__setBrakeFromVelocity()
            self.__showColor()

    def __showColor(self) -> None:
        self.__setColorIndicator()             # nastav barvy blinkrů
        self.__setColorOtherLights()           # nastav barvy ostatních světel
        self.__neopixels.write()             # zapiš nastavené barvy do led-ek

    def __setColorToOneLed(self, ledNo:int, color:list[int]) -> None:
        # nastav barvu pro jednu led-ku
        self.__neopixels[ledNo] = color

    def __setColor(self, ledList:list[int], color:list[int]) -> None:
        # nastav barvu pro seznam led-ek
        for ledNo in ledList:
            self.__setColorToOneLed(ledNo, color)

