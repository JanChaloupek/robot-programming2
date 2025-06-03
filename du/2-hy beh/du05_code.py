from HardwarePlatform import sleep, ticks_us, pin14, pin15, button_a, TWO_PI, TICKS_PER_CIRCLE, WHEEL_DIAMETER
from timer import Period

class DirectionEnum:
    # MicroPython neumi výčtový typ, toto je jeho náhrada
    LEFT = 1
    RIGHT = 2
    FORWARD = 3
    BACKWARD = 4

class MeasureUnit:
    TicksPerSecond = 11
    RevolutionsPerSecond = 12
    RadianPerSecond = 13
    MeterPerSecond = 14
    RevolutionsPerMinute = 23

class SpeedTicks:
    # Třída počítající rychlost z uložené historie tiků
    LIMIT = 50

    def __init__(self):
        self.__index = -1
        self.__times = [0] * self.LIMIT
        self.__ticks = [0] * self.LIMIT
        self.__countValues = -1
        self.__lastTime = None
        self.isStopped = True

    def getNewIndex(self, time_us: int) -> int:
        # Zjisti z casu jestli uz muzeme ulozit další data do historie
        newTime = int(time_us / 100_000)
        if newTime == self.__lastTime:
            return None
        else:
            self.__lastTime = newTime
            return (self.__index + 1) % self.LIMIT

    def isZeroChangeTicks(self, ticks:int) -> bool:
        # Je změna tiků nulová?
        diff = self.__ticks[self.__index] - ticks
        return diff == 0

    def nextValues(self, newIndex:int, time_us:int, ticks:int):
        # Ulož další data do historie
        if self.__countValues < self.LIMIT:
            self.__countValues += 1
        if self.__countValues > 2:
            self.isStopped = self.isZeroChangeTicks(ticks)
        self.__times[newIndex] = time_us
        self.__ticks[newIndex] = ticks
        self.__index = newIndex

    def update(self, ticks):
        time_us = ticks_us()
        newIndex = self.getNewIndex(time_us)
        if newIndex is not None:
            self.nextValues(newIndex, time_us, ticks)

    def calculate(self, count:int, offset:int):
        # Spočti rychlost v tikách za sekundu.
        # Použij na to count dat z historie a použij ty, které jsou offset staré
        if count < 2:
            count = 10
        if count + offset >= self.__countValues:
            count = self.__countValues - offset - 1
        if count < 2:
            return 0
        speed0 = self.__calculate(count, offset)
        speed1 = self.__calculate(count, offset + 1)
        return (speed0 + speed1) / 2

    def __calculate(self, count:int, offset:int):
        # Skutečné spočtení rychlosti (bez kontrol a průměrování) v tikách za sekundu
        endIndex = (self.__index - offset) % self.LIMIT
        startIndex = (endIndex - count + 1) % self.LIMIT
        diffTimes = self.__times[endIndex] - self.__times[startIndex]
        diffTicks = self.__ticks[endIndex] - self.__ticks[startIndex]
        return 1_000_000 * diffTicks / diffTimes

class Encoder:
    # Třída počítající tiky enkoderu
    def __init__(self, place:int, ticksPerCircle:int, radius:float):
        self.ticks = 0
        self.__isForward = True
        if place == DirectionEnum.LEFT:
            self.__pin = pin14
        else:
            self.__pin = pin15
        self.__ticksPerCircle = ticksPerCircle
        self.__radius = radius
        self.__speedTicks = SpeedTicks()
        self.__oldValue = self.readPin()

    def isStopped(self) -> bool:
        # je detekované že (asi) stojíme?
        return self.__speedTicks.isStopped

    def readPin(self) -> int:
        # přečti hodnotu pin-u z enkoderu
        return self.__pin.read_digital()

    def nextTick(self) -> None:
        # vyreš další tik (přičtení/odečtení)
        if self.__isForward:
            self.ticks += 1
        else:
            self.ticks -= 1

    def update(self, isForward:bool) -> None:
        self.__isForward = isForward
        newValue = self.readPin()
        if newValue != self.__oldValue:
            self.nextTick()
            self.__oldValue = newValue
        self.__speedTicks.update(self.ticks)

    def getSpeed(self, unit:int, count:int=3, offset:int=0) -> float:
        # dej mi rychlost v požadované jednotce rychlosti
        speed = self.__speedTicks.calculate(count, offset)
        if unit == MeasureUnit.TicksPerSecond:
            return speed
        speed /= self.__ticksPerCircle
        if unit == MeasureUnit.RevolutionsPerSecond:
            return speed
        if unit == MeasureUnit.RevolutionsPerMinute:
            # otáčky za sekundu * 60 sekund (v minutě)
            return speed*60
        speed *= TWO_PI
        if unit == MeasureUnit.RadianPerSecond:
            return speed
        speed *= self.__radius
        if unit == MeasureUnit.MeterPerSecond:
            return speed
        
        # neznámá jednotka
        return None

if __name__ == "__main__":

    encoder = Encoder(DirectionEnum.LEFT, TICKS_PER_CIRCLE, WHEEL_DIAMETER)
    printTimer = Period(timeout_ms=1_000)

    while not button_a.was_pressed():
        encoder.update(True)
        sleep(5)
        if printTimer.isTime():
            print(encoder.ticks, encoder.getSpeed(MeasureUnit.RadianPerSecond))
