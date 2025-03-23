from HardwarePlatform import button_a, ticks_ms, ticks_us, display
from systempicoed import System
from SM import AbstractSM, Task, Step
from du03_engine import Engine
from senzors import Senzors
from timer import Timer, Period

class LineSM(AbstractSM):
# Prechod mezi stavy v tomto stavovem automatu:
#                        -----------------------------
#                       |            -------------    |
#                       |         ->| turn left   |-->|
#                       v        /   -------------    |
#   -------     ----------------     -------------    |
#  | start |-->| line situation |-->| go straight |-->|
#   -------     ----------------     -------------    |
#      ^                |        \   -------------    |
#      |                v         ->| turn right  |-->
#      |             ------          -------------
#       <-----------| lost |
#                    ------ 
    # __state_start - inicializovan v predkovi
    __state_LineSituation = Task('lineSituation', tick_time=10)
    __state_GoStraight = Task('goStraight')
    __state_TurnRight = Task('turnRight')
    __state_TurnLeft = Task('turnLeft')
    __state_Lost = Step('lost', tick_time=5_000)
    # hodnoty pwm pro rizeni jizdy
    __normalPwm = 150   # pro jizdu rovne
    __smallPwm = 60     # pomalejsi kolo pri zataceni
    __maxPwm1 = 170     # rychlejsi kolo pri zataceni
    __maxPwm2 = 200     # rychlejsi kolo pri zataceni (pri velmi velke odchylce od tredu cary)
    __turnKoef = 0

    __printPeriod = Period()

    def __init__(self, senzors: Senzors, left: Engine, right: Engine):
        # kontruktor stavove masiny
        self.__senzors = senzors
        self.__leftEngine = left
        self.__rightEngine = right
        super().__init__()
        # self.debug = True

    def __start__init(self) -> None:
        System.display_drive_mode('s')
        self.setTickTime(100)
        print('Cekame na stisknuti tlacitka A')

    def __start(self) -> None:
        # stav start - cekame na tlacitko ktere nam povoli jizdu
        if button_a.was_pressed():
            # az po stisknuti tlacitka A se rozjedeme (jinak cekame)
            self.nextTask(self.__state_LineSituation)
            print('Tlacitka A stisknuto -> zaciname')

    __lostTime = Timer()  # casovac, kterym merim delku "ztraceni" (robot nevidi caru)

    def __lineSituation__init(self) -> None:
        self.__lostTime.stopTimer()

    def __lineSituation(self) -> None:
        direction = self.__senzors.getLineDirection()
        if direction is None:
            # nemam caru (budu cekat 3s jestli ji nahodou nechytime)
            if not self.__lostTime.isStarted():
                self.__lostTime.startTimer()
            if self.__lostTime.isTimeout(timeout_ms=3_000):
                # uz to trva moc dlouho (ztratili jsme se)
                self.nextTask(self.__state_Lost)
            return
        self.__turnKoef = abs(direction)
        if direction > 1:
            # caru detekovali leve senzory -> zatacej doleva
            self.nextTask(self.__state_TurnLeft)
            return
        if direction < -1:
            # caru detekovali prave senzory -> zatacej doprava
            self.nextTask(self.__state_TurnRight)
            return
        # caru mame prave uprosted -> zkusime jet chvili rovne
        self.nextTask(self.__state_GoStraight)
        return

    def __goStraight(self) -> None:
        self.__leftEngine.writePWM(self.__normalPwm)
        self.__rightEngine.writePWM(self.__normalPwm)
        System.display_drive_mode('|')
        self.nextTask(self.__state_LineSituation)

    def __turnLeft(self) -> None:
        # pro zataceni vlevo musime levym kolem tocit mene
        self.__leftEngine.writePWM(self.__smallPwm)
        self.__rightEngine.writePWM(self.__maxPwm2 if self.__turnKoef > 3 else self.__maxPwm1)
        System.display_drive_mode('\\')
        self.nextTask(self.__state_LineSituation)

    def __turnRight(self) -> None:
        # pro zataceni vpravo musime pravym kolem tocit mene
        self.__leftEngine.writePWM(self.__maxPwm2 if self.__turnKoef > 3 else self.__maxPwm1)
        self.__rightEngine.writePWM(self.__smallPwm)
        System.display_drive_mode('/')
        self.nextTask(self.__state_LineSituation)

    def __lost(self) -> None:
        self.__leftEngine.stop()
        self.__rightEngine.stop()
        System.display_drive_mode('x')
        print('Ztratili jsme se.')
        self.nextTask(self.__state_start, skipTimeout=False)

    def __end__init(self) -> None:
        System.display_drive_mode('E')
        print('Konec')