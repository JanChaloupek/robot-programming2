from HardwarePlatform import sleep, pin14, pin15, button_a
from timer import Period

class DirectionEnum:
    # MicroPython neumi výčtový typ, toto je jeho náhrada
    LEFT = 1
    RIGHT = 2
    FORWARD = 3
    BACKWARD = 4

class Encoder:
    # Třída počítající tiky enkoderu
    def __init__(self, place:int):
        self.ticks = 0
        self.__isForward = True
        if place == DirectionEnum.LEFT:
            self.__pin = pin14
        else:
            self.__pin = pin15
        self.__oldValue = self.readPin()

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

if __name__ == "__main__":

    encoder = Encoder(DirectionEnum.LEFT)
    printTimer = Period(timeout_ms=1_000)

    while not button_a.was_pressed():
        encoder.update(True)
        sleep(5)
        if printTimer.isTime():
            print(encoder.ticks)
