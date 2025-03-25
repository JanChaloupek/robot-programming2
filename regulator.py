from timer import Period

class RegulatorP(Period):
    # třída implementující P-regulátor
    def __init__(self, p:float, timeout_ms:int) -> None:
        self.__k = p
        super().__init__(timeout_ms)

    def dT(self, time_ms:int) -> float:
        return self.getTimeDiff(time_ms) / 1000

    def k(self, time_ms: int) -> float:
        return self.__k * self.dT(time_ms)

    def getActionIntervention(self, time_ms:int, inputNominal:float, inputActual:float) -> float:
        # vypočti akční zásah
        error = inputNominal - inputActual
        changeValue = self.k(time_ms) * error
        return changeValue
    
class RegulatorPID(RegulatorP):

    def __init__(self, p:float, i:float, d:float, timeout_ms:int) -> None:
        RegulatorP.__init__(self, p, timeout_ms)
        self.__i = i
        self.__d = d

    def getActionIntervention(self, time_ms:int, inputNominal:float, inputActual:float) -> float:
        #TODO: dodelat
        pass
