from HardwarePlatform import i2c, I2C_ADDR_SENZORS, ticks_diff, ticks_ms
from directions import DirectionEnum
from systempicoed import System
from timer import Timer

class LineSituationEnum:
    Line = 1
    CrossRoads = 2

class Senzors(Timer):
    # třída vyčítající senzory po i2c a jejich získání dotazem
    ObstaleRight = 0x40
    ObstaleLeft = 0x20

    LT_Count = 6  # počet senzorů čáry (kód počítá s hodnotami 3, 4, 5 nebo 6)

    LT_FarRight = 0x02
    LT_Right = 0x10
    LT_MiddleRight = 0x80
    LT_MiddleLeft = 0x08
    LT_Left = 0x04
    LT_FarLeft = 0x01

    LT_Central = 0x08
    LT_RightCross56 = LT_Right | LT_FarRight
    LT_LeftCross56 = LT_Left | LT_FarLeft
    LT_RightCross4 = LT_Right | LT_MiddleRight
    LT_LeftCross4 = LT_Left | LT_MiddleLeft
    LT_RightCross3 = LT_Right | LT_Central
    LT_LeftCross3 = LT_Left | LT_Central
    LT_All = 0x9F

    def __init__(self) -> None:
        super().__init__(timeout_ms=50)
        self.__data = -1
        self.senzorDataUpdate()
        self.__timerNotLine = Timer(timeout_ms=3_000)
        self.__timerNotLine.stopTimer()

    def getMiddleSenzorsAddr(self) -> int:
        if (Senzors.LT_Count % 2) == 0:
            return Senzors.LT_MiddleLeft | Senzors.LT_MiddleRight
        else:
            return Senzors.LT_Central

    def show(self, bh:int=2, bl:int=1) -> None:
        # zobraz stav vyčtených senzorů na displeji
        farLeft = None
        farRight = None
        midleLeft = None
        midle35 = None
        midleRight = None

        if Senzors.LT_Count >= 5:
            farRight = self.getSenzor(Senzors.LT_FarRight)
            farLeft = self.getSenzor(Senzors.LT_FarLeft)

        if (Senzors.LT_Count % 2) == 0:
            midleLeft = self.getSenzor(Senzors.LT_MiddleLeft)
            midleRight = self.getSenzor(Senzors.LT_MiddleRight)
        else:
            midle35 = self.getSenzor(Senzors.LT_Central)

        obstacleLeft = self.getSenzor(Senzors.ObstaleLeft)
        left = self.getSenzor(Senzors.LT_Left)
        right = self.getSenzor(Senzors.LT_Right)
        obstacleRight = self.getSenzor(Senzors.ObstaleRight)

        System.display_senzors(
            obstacleLeft, 
            farLeft, left, 
            midleLeft, midle35, midleRight, 
            right, farRight, 
            obstacleRight, 
            bh, bl
        )

    def senzorDataUpdate(self, time:int=None) -> None:
        # přečti data po i2c
        self.__dataPrev = self.__data
        self.__data = i2c.read(I2C_ADDR_SENZORS, 1)[0] ^ Senzors.LT_All
        self.startTimer(time)
        if self.__data != self.__dataPrev:
            self.show(255,1)

    def getData(self, mask:int) -> int:
        return self.__data & mask

    def getSenzor(self, senzor:int) -> bool:
        # je senzor aktivní? (= ve stavu 0) - pokud je senzorů více musí být všechny aktivní
        return self.getData(senzor) == 0

    def getAnySenzor(self, senzor:int) -> bool:
        # je alespoň jeden ze senzorů aktivní?
        return self.getData(senzor) != senzor
    

    def update(self) -> None:
        time = ticks_ms()
        if self.isTimeout(time):
            self.senzorDataUpdate(time)

    def getTypeCrossRoads(self) -> int:
        # detekujeme křižovatku zatáčející vlevo (+1) nebo vpravo (+2)? 0 = nejsme na křižovatce
        # podle počtu senzorů se berou pro detekci jiné senzory (vždy se vyberou 2 nejkrajnějš) 
        if Senzors.LT_Count >= 5:
            LeftCross = Senzors.LT_LeftCross56
            RightCross = Senzors.LT_RightCross56
        elif Senzors.LT_Count == 4:
            LeftCross = Senzors.LT_LeftCross4
            RightCross = Senzors.LT_RightCross4
        else:  # máme pouze 3 senzory čáry
            LeftCross = Senzors.LT_LeftCross3
            RightCross = Senzors.LT_RightCross3
        typeCross = 0
        if self.getSenzor(LeftCross):
            typeCross += DirectionEnum.LEFT
        if self.getSenzor(RightCross):
            typeCross += DirectionEnum.RIGHT
        return typeCross            

    def getLineDirection(self) -> int:
        # jsme někde na čáře?
        # pro 6 senzorů čáry kód umí detekovat 9 různých pozicí a podle toho různě rychle zatáčet:
        # None = nejsme na čáře
        # 0    = jsme na středu (jed rovně)
        # +- 1 = malý požadavek na zatáčení (vnitřní senzory - pokud jsou dva)
        # +- 2 = střední požadavek na zatáčení (vnitřní a střední senzory)
        # +- 3 = velký požadavek na zatáčení (střední senzory)
        # +- 6 = super velký požadavek na zatáčení (krajní senzory)
        # kladne jsou leve senzory (potřebujeme zahnout doleva)
        # zaporne jsou pravé senzory (potřebujeme zahnout doprava)
        if Senzors.LT_Count >= 5: # existují krajní (Far) senzory čáry
            if self.getSenzor(Senzors.LT_FarLeft):
                return 6
            if self.getSenzor(Senzors.LT_FarRight):
                return -6

        if (Senzors.LT_Count % 2) == 0:  # máme uprostřed 4 senzory čáry 
            if self.getSenzor(Senzors.LT_Left) and not self.getSenzor(Senzors.LT_MiddleLeft):
                return 3
            if self.getSenzor(Senzors.LT_Right) and not self.getSenzor(Senzors.LT_MiddleRight):
                return -3
            if self.getSenzor(Senzors.LT_Left | Senzors.LT_MiddleLeft):
                return 2
            if self.getSenzor(Senzors.LT_Right | Senzors.LT_MiddleRight):
                return -2
            if self.getSenzor(Senzors.LT_MiddleLeft) and not self.getSenzor(Senzors.LT_MiddleRight):
                return 1
            if self.getSenzor(Senzors.LT_MiddleRight) and not self.getSenzor(Senzors.LT_MiddleLeft):
                return -1
            if self.getSenzor(Senzors.LT_MiddleRight | Senzors.LT_MiddleLeft):
                return 0
        else:
            if self.getSenzor(Senzors.LT_Left):
                return 3
            if self.getSenzor(Senzors.LT_Right):
                return -3
            if self.getSenzor(Senzors.LT_MiddleOdd):
                return 0
        # nevidíme pod sebou nikde čáru (vyjeli jsme mimo čáru)
        return None

    def getSituationLine(self) -> int:
        # detekujeme křížovateku?
        if self.getTypeCrossRoads() > 0:
            self.__timerNotLine.stopTimer()
            return LineSituationEnum.CrossRoads
        
        # detekujeme čáru?
        if self.getLineDirection() is not None:
            self.__timerNotLine.stopTimer()
            return LineSituationEnum.Line
        
        # jsme mimo čáru
        if not self.__timerNotLine.isStarted():
            # pokud jeste nemerime cas "mimo caru", tak zacneme
            self.__timerNotLine.startTimer()

        if not self.__timerNotLine.isTimeout():
            # zatím je to krátký čas (ještě budeme tvrdit, že jsme na čáře)
            return LineSituationEnum.Line

        # uz je to moc dlouho -> ztratili jsme se
        return None
