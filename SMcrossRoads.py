from HardwarePlatform import ticks_ms, sleep, PI, button_b, Display
from soundSubsystem import brzdeni, tutu, hello
from senzors import LineSituationEnum
from SM import AbstractSM, Task, Step
from lightSubsystem import BeamsEnum
from directions import DirectionEnum
from position import Position
from robot import Robot

class Commands:
    # seznam prikazu a index k jeho precteni
    index = 0
    list = [
        DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.LEFT,
        DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.LEFT,
        DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.LEFT,
        DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.FORWARD, DirectionEnum.LEFT,
    ]

    def get(self) -> DirectionEnum:
        if (self.index < len(self.list)) and self.index >= 0:
            return self.list[self.index]
        return None
    
    def next(self) -> None:
        self.index += 1

class CrossRoads(AbstractSM):

    # seznam prikazu a index k jeho precteni
    commands = Commands()

    # objekt pocitajici pozici robota (inicializacni hodnota je x=0, y=0, theta=0)
    position = Position()

    def __init__(self, robot: Robot, tasks=None, tick_time=None) -> None:
        self.__robot = robot
        super().__init__(tasks, tick_time)
        self.debug = True

    def log(self, message: str) -> None:
        print(message)
        # lcd.clear()
        # lcd.putstr(message)

    # Task('start') - definovano v AbstractSM
    def __start__init(self):
        # inicializace stavu start (zobraz ikonu na displeji a nastav tickTime)
        self.log('Zaciname, stiskni B')
        Display.drive_mode('s')
        self.setTickTime(300)

    def __start(self):
        # opakujici se metoda pro stav start (zaciname stiskem tlacitka B)
        if button_b.was_pressed():
            self.log('Nastartuj')
            self.nextTask(self.STEP_nastartuj)

    STEP_nastartuj = Step('nastartuj', tick_time=2_000)
    def __nastartuj(self):
        # jednorazove nastartujeme, rozsvitime svetla a zatroubime
        Display.drive_mode('|')
        self.position.showOnDisplay()
        self.__robot.lightsControl.main = BeamsEnum.DippedBeams
        self.__robot.playHonk(tutu)
        # po nastartovani budeme sledovat caru
        self.nextTask(self.TASK_sledujCaru)

    TASK_sledujCaru = Task('sleduj_caru')
    def __sleduj_caru__init(self):
        self.log('Sleduj caru')
        if self.commands.get() is None:
            # už nemáme žádné příkazy, tak jsme úspěšně splnili úkol
            self.endTask()

    def __sleduj_caru(self):
        situation = self.__robot.getSituationLine()
        if situation == LineSituationEnum.CrossRoads:
            self.nextTask(self.STEP_krizovatka)
        elif situation == LineSituationEnum.Line:
            self.__robot.rideLine()
        else:
            self.nextTask(self.STEP_ztracen)

    STEP_krizovatka = Step('krizovatka', tick_time=2_000)
    def __krizovatka(self):
        self.log('Krizovatka')
        Display.drive_mode('I+')
        self.__robot.playHonk(brzdeni)
        self.__robot.motionControl.stop()
        # prave jsme dorazili na krizovateku, takze pozici rekneme ze jsme jeli o 1čku dopredu
        self.position.move_forward()
        self.position.showOnDisplay()
        # posuneme se na dalsi prikaz a precteme ho
        self.command = self.commands.get()
        self.commands.next()
        # dalsim stavem je popojed
        self.nextTask(self.TASK_popojed)

    TASK_popojed = Task('popojed', tick_time=10) # exitingCrossRoads() nemá definovanou periodu, proto je perioda zde
    def __popojed__init(self):
        Display.drive_mode('_')
        self.__robot.exitCrossRoads_start()

    def __popojed(self):
        success = self.__robot.exitCrossRoads(self.command)
        if success:
            if self.command == DirectionEnum.FORWARD:
                self.nextTask(self.TASK_sledujCaru, skipTimeout=False)
                Display.drive_mode('|')
            else:
                self.nextTask(self.TASK_zatoc, skipTimeout=False)

    TASK_zatoc = Task('zatoc', tick_time=10) # turningToLine() nemá definovanou periodu, proto je perioda zde
    def __zatoc__init(self):
        self.__robot.turningToLine_start()
        if self.command == DirectionEnum.LEFT:
            Display.drive_mode('TL')
        if self.command == DirectionEnum.RIGHT:
            Display.drive_mode('TR')
        
    def __zatoc(self):
        if self.__robot.turningToLine(self.command, 0.1):
            self.nextTask(self.TASK_sledujCaru)
            Display.drive_mode('|')

    def __zatoc__done(self):
        if self.command == DirectionEnum.LEFT:
            self.position.turn_left()
        if self.command == DirectionEnum.RIGHT:
            self.position.turn_right()

    STEP_ztracen = Step('ztracen', tick_time=2_000)
    def __ztracen(self):        
        self.__robot.stop()
        self.__robot.lightsControl.main = None
        Display.drive_mode('x')
        self.startTask()

    # Step('end') - definovano v AbstractSM    
    def __end__init(self):
        Display.drive_mode('E')
        self.__robot.stop()
        self.__robot.lightsControl.main = None
        self.__robot.playHonk(hello)
