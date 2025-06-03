from board import P8, P12
from digitalio import Direction 
from time import monotonic_ns
from ultrazvuk.cas import Timer
from digitalio import DigitalInOut

class Ultrazvuk:
    def __init__(self, trig:DigitalInOut, echo:DigitalInOut):
        self.__trigger = trig
        self.__trigger.direction = Direction.OUTPUT
        self.__echo = echo
        self.__rychlost_zvuku = 343 # m/s
        self.__sendingTimer = Timer(False)
        self.__measureTimer = Timer(False)
    
    def __sendSignal(self):
        self.__trigger.value = True
        self.__trigger.value = False
        self.__sendingTimer.startTimer()
    
    def __reset(self):
        self.__sendingTimer.stopTimer()
        self.__measureTimer.stopTimer()

    def spocti_vzdalenost(self):
        ubehnuty_cas = self.__measureTimer.getTimeDiff() / 1_000_000_000 # prevod na sekundy
        return ubehnuty_cas*self.__rychlost_zvuku/2.0

    def proved_mereni_blokujici(self, timeout): 
        self.__sendSignal()
        while self.__echo.value == 0:
            if self.__sendingTimer.isTimeout(timeout):
                self.__reset()
                return -2  # Timeout
            
        self.__measureTimer.startTimer()
        while self.__echo.value == 1:
            if self.__measureTimer.isTimeout(timeout):
                self.__reset()
                return -1  # Timeout

        return self.spocti_vzdalenost()

    def proved_mereni_neblokujici(self, timeout = 1):
        if not self.__sendingTimer.isStarted():
            self.__sendSignal()
        elif not self.__measureTimer.isStarted():
            if self.__echo.value == 0:
                if self.__sendingTimer.isTimeout(timeout):
                    self.__reset()
                    return -2  # Timeout
            else:
                self.__measureTimer.startTimer()
        else:
            if self.__echo.value == 1:
                if self.__measureTimer.isTimeout(timeout):
                    self.__reset()
                    return -1  # Timeout
            else:
                # impuls na echo skončil 0 -> 1 -> 0 (spočítáme vzdálenost)
                return self.spocti_vzdalenost()
        return -3  # continue
