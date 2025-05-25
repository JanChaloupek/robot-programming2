from HardwarePlatform import ticks_ms
from velocity import Velocity
from regulator import RegulatorP


class  Tempomat:

    # vzdalenost kterou ma tempomat udrzovat (None = vypnutý tempomat)
    distance: float = None
    acceptableDistanceDiff: float = 0.03
    # regulator, ktery bude udrzovat vzdalenost od prekazky (predchoziho auta)
    __regulator = RegulatorP(p=1, timeout_ms=500)

    def isActivate(self) -> bool:
        # je tempomat aktivovany (ma nastavenou vzdálenost)?
        return self.distance is not None

    def __isAcceptableDistanceDiff(self, actualDistance:float) -> bool:
        # jsme v přijatelné vzdálenosti od překážky?
        distanceDif = abs(actualDistance - self.distance)
        return distanceDif <= self.acceptableDistanceDiff

    def getSpeedFromDistance(self, time:int, actualDistance:float) -> float:
        # spocti novou doprednou rychlost aby tempomat udrzel vzdalenost
        if self.__isAcceptableDistanceDiff(actualDistance):
            # vzdalenost je akceptovatelna = spust znovu casovac a pozaduj nulovou rychlost (zastav robota)
            self.__regulator.startTimer(time)
            return 0.0
        else:
            # vypocti rychlost pomoci regulatoru
            return self.__regulator.getActionIntervention(
                time, -self.distance, -actualDistance
            )

    def calculateSpeed(self, actualDistance: float) -> float:
        if self.isActivate():
            # tempomat je aktivovan (má nastavenou vzdálenost, kterou ma udržovat)
            time = ticks_ms()
            if self.__regulator.isTimeout(time):
                # už je čas vypočítat novou rychlost (potřebujeme k tomu rozdíl času od posledního výpočtu)
                return self.getSpeedFromDistance(time, actualDistance)
        
        # nemame regulovat rychlost
        return None
        
