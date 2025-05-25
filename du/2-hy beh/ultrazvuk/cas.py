from time import monotonic
from adafruit_ticks import ticks_ms, ticks_diff

class Timer:
    def __init__(self, start:bool=True):
        if start:
            self.startTimer()
        else:
            self.stopTimer()

    def startTimer(self):
        # spust časovač	
        self.__startTime = monotonic()

    def stopTimer(self):
        # zastav časovač
        self.__startTime = None

    def isStarted(self) -> bool:
        # je časovač spuštěn?
        return self.__startTime is not None

    def getTimeDiff(self) -> int:
        return ticks_diff(monotonic(), self.__startTime)

    def isTimeout(self, timeout: int) -> bool:
        # vyprsel timeout casovace?
        if not self.isStarted():
            return False
        return self.getTimeDiff() >= timeout
    