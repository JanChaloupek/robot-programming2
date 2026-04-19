from HardwarePlatform import TWO_PI, HALF_PI, PI, Display
from timer import Timer
from math import cos, sin, atan2, sqrt, degrees, pi

PI = pi	
TWO_PI = 2*pi
HALF_PI = pi/2
class Point:
    x: float
    y: float

    def __init__(self, x:float=0.0, y:float=0.0) -> None:
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return "x: " + str(self.x) + " y: " + str(self.y)

    def distance(self, point: 'Point') -> float:
        return sqrt((point.y - self.y)**2 + (point.x - self.x)**2)

    def angle(self, point) -> float:
        return atan2(point.y - self.y, point.x - self.x)

class Position(Point):
    theta: float

    def __init__(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> None:
        super().__init__(x, y)
        self.theta = theta

    def __str__(self) -> str:
        return super().__str__() + " theta:" + str(degrees(self.theta))

    def __move(self, distance:float) -> None:
        self.x += distance * cos(self.theta)
        self.y += distance * sin(self.theta)

    def __turn(self, angle:float) -> None:
        self.theta += angle
        self.__normalizeTheta()

    def __normalizeTheta(self) -> None:
        self.theta = self.theta % TWO_PI
        if self.theta > PI:
            self.theta -= TWO_PI

    def move_forward(self, distance:float=1.0) -> None:
        self.__move(distance)

    def move_backward(self, distance:float=1.0) -> None:
        self.__move(-distance)

    def turn_left(self, angle:float=HALF_PI) -> None:
        self.__turn(angle)

    def turn_right(self, angle:float=HALF_PI) -> None:
        self.__turn(-angle)

    def showOnDisplay(self) -> None:
        x = round(self.x)
        y = round(self.y)
        theta =  round(degrees(self.theta))
        # lcd.writePosition(x, y, theta)
        Display.position(x, y)


class Odometry(Position):

    def odometry_init(self, wheelbase:float, wheelRadius:float, ticksPerCircle:int, init:Position=None) -> None:
        self.__odometryTimer = Timer(50)
        self.__wheelbase = wheelbase
        self.__const = TWO_PI * wheelRadius / ticksPerCircle
        if init is None:
            init = Position()
        self.initPosition = init
        self.odometry_reinit()

    def odometry_reinit(self) -> None:
        self.x = self.initPosition.x
        self.y = self.initPosition.y
        self.theta = self.initPosition.theta

    def odometry_calculate(self, deltaTicks:tuple[int,int]) -> None:
        leftTicks, rightTicks = deltaTicks
        # lokalizace v obecnem prostoru pro diferencialni podvozek
        deltaX     = self.__const * (rightTicks + leftTicks) / 2
        deltaTheta = self.__const * (rightTicks - leftTicks) / self.__wheelbase
        # pocitame smer jako by jsme se otocili o polovinu zmeny theta
        calculateTheta = self.theta + deltaTheta / 2
        # posun v obecnem prostoru
        self.x += cos(calculateTheta) * deltaX
        self.y += sin(calculateTheta) * deltaX
        self.theta += deltaTheta        
        self.__normalizeTheta()

    def calculate_directionToPoint(self, goal:Point) -> tuple[float, float]:
        # spocti vzdalenost a smer k cili
        distance = self.distance(goal)
        goalTheta = self.angle(goal)
        deltaTheta = goalTheta - self.theta
        return distance, deltaTheta

    def isTimeout(self, time:int=None) -> bool:
        return self.__odometryTimer.isTimeout(time)
    
    def odometry_startTimer(self, time:int=None) -> None:
        self.__odometryTimer.startTimer(time)