from HardwarePlatform import TWO_PI, HALF_PI, PI
from timer import Timer
from math import cos, sin, atan2, sqrt, degrees

class Point:
    x: float
    y: float

    def __str__(self) -> str:
        return "x: " + str(self.x) + " y: " + str(self.y)

    def distance(self, point) -> float:
        return sqrt((self.x - point.x)**2 + (self.y - point.y)**2)

    def angle(self, point) -> float:
        return atan2(point.y - self.y, point.x - self.x)

class Position:
    point: Point
    theta: float

    def __init__(self, x:float=0.0, y:float=0.0, theta:float=0.0) -> None:
        self.point = Point()
        self.point.x = x
        self.point.y = y
        self.theta = theta

    def __copyPosition(self, copyFrom) -> None:
        self.point.x = copyFrom.point.x
        self.point.y = copyFrom.point.y
        self.theta = copyFrom.theta

    def __str__(self) -> str:
        return "x:" + str(self.point.x) + " y:" + str(self.point.y) + " theta:" + str(degrees(self.theta))

    def move_forward(self, distance:float=1.0) -> None:
        self.point.x += distance * cos(self.theta)
        self.point.y += distance * sin(self.theta)

    def move_backward(self, distance:float=1.0) -> None:
        self.point.x -= distance * cos(self.theta)
        self.point.y -= distance * sin(self.theta)

    def __normalizeTheta(self) -> None:
        self.theta = self.theta % TWO_PI
        if self.theta > PI:
            self.theta -= TWO_PI

    def __turn(self, angle:float) -> None:
        self.theta += angle
        self.__normalizeTheta()

    def turn_left(self, angle:float=HALF_PI) -> None:
        self.__turn(angle)

    def turn_right(self, angle:float=HALF_PI) -> None:
        self.__turn(-angle)


class Odometry(Position):

    def odometry_init(self, wheelbase:float, wheelRadius:float, ticksPerCircle:int, init:Position=None) -> None:
        self.__odometryTimer = Timer(50)
        self.__wheelbase = wheelbase
        self.__const = TWO_PI * wheelRadius / ticksPerCircle
        if init is None:
            init = Position(x=0.0, y=0.0, theta=0.0)
        self.initPosition = init
        self.odometry_reinit()

    def odometry_reinit(self) -> None:
        self.__copyPosition(self.initPosition)

    def odometry_calculate(self, deltaTicks:tuple[int,int]) -> None:
        leftTicks, rightTicks = deltaTicks
        # lokalizace v obecnem prostoru pro diferencialni podvozek
        deltaX     = self.__const * (rightTicks + leftTicks) / 2
        deltaTheta = self.__const * (rightTicks - leftTicks) / self.__wheelbase
        # pocitame smer jako by jsme se otocili o polovinu zmeny theta
        calculateTheta = self.theta + deltaTheta / 2
        # posun v obecnem prostoru
        self.point.x += cos(calculateTheta) * deltaX
        self.point.y += sin(calculateTheta) * deltaX
        self.theta += deltaTheta        
        self.__normalizeTheta()

    def calculate_directionToPoint(self, goal:Point) -> tuple[float, float]:
        # spocti vzdalenost a smer k cili
        distance = self.point.distance(goal)
        goalTheta = self.point.angle(goal)
        deltaTheta = goalTheta - self.theta
        return distance, deltaTheta

    def isTimeout(self, time:int=None) -> bool:
        return self.__odometryTimer.isTimeout(time)
    
    def odometry_startTimer(self, time:int=None) -> None:
        self.__odometryTimer.startTimer(time)