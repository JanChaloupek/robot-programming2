from HardwarePlatform import ticks_ms
from timer import Period
# volani metod pro tridu Task a Step
# ----------------------------------------------------
# Task:                              Step:
#  __{name1}__init                   __{name1}__init
#           0 [ms]                             0 [ms]
#  __{name1}                           
#           tickTime [ms]
#  __{name1}                           
#           tickTime [ms]
#  .... 
#  __{name1}                          __{name1}
#           tickTime or 0 [ms]                 tickTime or 0 [ms]
#  __{name1}__done                    __{name1}__done
#           0 [ms]                             0 [ms]
#  __{name2}__init                    __{name2}__init

class CPU:
    __NO = 0
    __Q = {}

    @staticmethod
    def add(sm: 'AbstractSM', cpu_no_parent:int=None) -> 'AbstractSM':
        CPU.__NO += 1
        sm.cpu_no = CPU.__NO
        CPU.__Q[CPU.__NO] = [sm, cpu_no_parent]
        sm.run()
        return sm

    @staticmethod
    def parentOf(cpu_no: int) -> 'AbstractSM':
        if cpu_no not in CPU.__Q:
            return None
        cpu_no_parent = CPU.__Q[cpu_no][1]
        if cpu_no_parent is None or cpu_no_parent not in CPU.__Q:
            return None
        return CPU.__Q[cpu_no_parent][0]

    @staticmethod
    def remove(cpu_no: int) -> None:
        del CPU.__Q[cpu_no]

    @staticmethod
    def tick() -> None:
        for k, n in CPU.__Q.items():
            n[0].tick()

    @staticmethod
    def existSM() -> bool:
        return len(CPU.__Q) > 0

class Task:
    def __init__(self, name:str, tick_time:int=None) -> None:
        self.id = None
        self.name = name
        self.tickTime = tick_time
        self.autoNext = False

    def __str__(self) -> str:
        return self.name

class Step(Task):
    def __init__(self, name:str, tick_time:int=None) -> None:
        super().__init__(name, tick_time)
        self.autoNext = True

class AbstractSM:
    # stavy definovane v kazdem stavovem automatu
    __state_failure = Step('failure')
    __state_start = Task('start')
    __state_end = Step('end')

    INIT_SUFFIX = '__init' # provolani teto metody pred tim nez se dostaneme do stavu (vyresisit "předpoklady")
    DONE_SUFFIX = '__done' # provoleni teto metody po tom co opustime stav (uklizeni po sobe) - pred dalsim stavem

    def __init__(self, tasks: list[Task]=None, tick_time_default:int=None) -> None:
        self.__period = Period()
        self.__stack = []
        self.__curTask = None  # type: Task|None
        self.__nextTask = None # type: Task|None
        self.cpu_no = None     # type: int|None
        self.__running = False
        self.__tic = 0         # Task Id Counter
        self.debug = False
        if not isinstance(tasks, list):
            # pokud nemame urceny seznam Tasku, zaciname Taskem start
            tasks = [self.__state_start]
        self.setTasks(tasks, tick_time_default)

    def __start(self) -> None:
        self.nextTask()

    def __end(self) -> None:
        self.__cleanSelf()

    def __cleanSelf(self) -> None:
        parent = CPU.parentOf(self.cpu_no)
        if parent:
            parent.cpu_child_done(self.cpu_no)
        CPU.remove(self.cpu_no)

    def add2CPU(self, sm: 'AbstractSM') -> 'AbstractSM':
        # prida noveho potomka do SQM
        return CPU.add(sm, self.cpu_no)

    def cpu_child_done(self, cpu_no: int) -> None:
        # bude provolana, kdykoliv se dokonci ukoly v SQM potomkovi
        pass

    def run(self) -> None:
        # povole beh, nastav casovac, definuj task na rade
        self.__running = True
        self.__period.startTimer()
        self.nextTask()

    def nextTask(self, task:Task=None, skipTimeout:bool=None) -> None:
        if skipTimeout is None:
            # pokud neni Task predany, funguj postaru (bez preskoceni timeoutu)
            skipTimeout = task is not None
        if skipTimeout:
            self.__setPeriodTimeout(0)
        if task is not None:
            self.__nextTask = task
            return
        if self.__stack:
            self.__nextTask = self.__stack.pop(0)
            return
        # pokud uz zadnu Task nemame, spustime koncovy Task
        self.endTask()

    def endTask(self) -> None:
        self.__nextTask = self.__state_end

    def failureTask(self) -> None:
        self.__nextTask = self.__state_failure

    def tick(self) -> None:
        if self.__running is False:
            return
        if self.__period.isTime():
            if self.__nextTask is not None:
                # pokud je definovany pristi task, tak ho udelat aktualnim, nastav casovac a spust ho
                if self.__curTask is not None:
                    # pokud mame aktualni task, nejprve zavolame jeho ukonceni
                    self.__callStep(self.DONE_SUFFIX)
                # nastav tento novy task jako aktualni, dej mu nove id a spust 
                self.__curTask = self.__nextTask
                self.__nextTask = None
                self.__tic += 1
                self.__curTask.id = self.__tic
                
                self.__setPeriodTimeout(0)
                self.__callStep(self.INIT_SUFFIX)
                return
            
            if self.__curTask is not None:
                self.__setPeriodTimeout(self.__curTask.tickTime)
                # pokud mam aktualni Task, budeme volat jeho opakujici se metodu
                self.__callStep()
                if self.__curTask.autoNext:
                    # a pokud se mame automaticky prepnout na nasleduji task
                    if self.__nextTask is None:
                        # a nekdo jiny uz ho nedefinoval, definujeme ho my
                        self.nextTask()

    def setTasks(self, tasks: list[Task], tick_time_default:int) -> None:
        self.__period.startTimer()
        self.__tickTimeDefault = tick_time_default
        self.__stack = tasks if isinstance(tasks, list) else []
        if self.__running:
            self.nextTask()

    def __callStep(self, suffix: str = '') -> None:
        n = '__' + self.__curTask.name + suffix
        if hasattr(self, n):
            if self.debug:
                print(ticks_ms(), n)
            fce = getattr(self, n)
            fce()
        else:
            if self.debug:
                print(ticks_ms(), n, '    --SKIP')

    def __setPeriodTimeout(self, n:int) -> None:
        if n is None:
            n = self.__tickTimeDefault
        self.__period.timeout_ms = n

    def setTickTime(self, tickTime:int) -> None:
        if self.__curTask is not None:
            self.__curTask.tickTime = tickTime
