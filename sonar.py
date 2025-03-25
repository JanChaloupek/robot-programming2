from HardwarePlatform import pin8, pin12, time_pulse_us, ticks_ms, ticks_diff
from timer import Period

class Sonar(Period):
    # Třída implementující měření vzdálenosti k překážce
    MAX_DISTANCE = 1
    LIMIT = 5

    def __init__(self, timeout_ms=100) -> None:
        super().__init__(timeout_ms)
        self.__historyDistancies = [0] * self.LIMIT
        self.__index = 0
        self.__errorCount = 0
        self.__trigger = pin8
        self.__trigger.write_digital(0)
        self.__echo = pin12
        self.__echo.read_digital()
        self.lastDistance = None
        self.measureAndUseNewDistance()

    def measureDistance(self) -> float|int:
        # změř a vrať vzdálenost k překážce
        speed = 340    # m/s
        self.__trigger.write_digital(1)
        self.__trigger.write_digital(0)
        retValue = time_pulse_us(self.__echo, 1, 5_000)
        if retValue < 0:
            # nastala chyba pri mereni
            return retValue
        # vzdalenost = cas_s * rychlost / 2
        return (retValue / 1_000_000) * speed / 2

    def measureAndUseNewDistance(self) -> None:
        self.__lastReturned = self.measureDistance()
        if self.__lastReturned == -1:
            # tuto kontretni chybu prevedeme na maximalni vzdalenost
            self.__lastReturned = self.MAX_DISTANCE
        if self.__lastReturned < 0:
            # pokud porad mame chybu, zapocitej ji
            self.__errorCount += 1
        else:
            self.__errorCount = 0
            self.__historyDistancies[self.__index] = self.__lastReturned
            self.__index += 1
            if self.__index >= self.LIMIT:
                self.__index = 0
                self.lastDistance = self.__average()

    def __average(self) -> float:
        suma = 0.0
        for x in range(self.LIMIT):
            suma += self.__historyDistancies[x]
        return suma / self.LIMIT

    def isError(self) -> bool:
        return self.__errorCount > 10

    def update(self) -> None:
        if self.isTime():
            self.measureAndUseNewDistance()
