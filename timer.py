from HardwarePlatform import ticks_ms, ticks_diff

class Timer:
    # třída implementující casovac
    def __init__(self, timeout_ms:int=None, startTimer:bool=True) -> None:
        self.timeout_ms = timeout_ms
        if startTimer:
            self.startTimer()

    def __getTime(self, time_ms:int) -> int:
        # pokud nemas cas, vrat aktualni cas v ms
        if time_ms is None:
            time_ms = ticks_ms()
        return time_ms

    def __getTimeout(self, timeout_ms:int=None) -> int:
        if timeout_ms is None:
            timeout_ms = self.timeout_ms
        if timeout_ms is None:
            timeout_ms = 0
        return timeout_ms

    def startTimer(self, start_time_ms:int=None, timeout_ms:int=None) -> None:
        # spust časovač
        self.timeout_ms = timeout_ms
        self.__startTime = self.__getTime(start_time_ms)

    def stopTimer(self) -> None:
        # zastav časovač
        self.__startTime = None

    def isStarted(self) -> bool:
        # je časovač spuštěn?
        return self.__startTime is not None

    def isTimeout(self, test_time_ms:int=None, timeout_ms:int=None) -> bool:
        # vyprsel timeout casovace v case 'time_ms'?
        if not self.isStarted():
            return False
        diff_ms = ticks_diff(self.__getTime(test_time_ms), self.__startTime)
        return diff_ms >= self.__getTimeout(timeout_ms)

class Period(Timer):
    # třída implementující casovac, ktery se sam opakovane spousti po uplynuti timeoutu
    def isTime(self, test_time_ms:int=None, timeout_ms:int=None) -> bool:
        time_ms = self.__getTime(test_time_ms)
        ret = self.isTimeout(time_ms, timeout_ms)
        if ret:
            # pokud vyprsel cas, casovac znovu spustime (k casu testu)
            self.startTimer(time_ms)
        return ret
