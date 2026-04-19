# Soubor pripravujici nazvy funkci jake pouziva microbit
from adafruit_ticks import ticks_diff as adf_ticks_diff, ticks_ms as adf_ticks_ms
from picoed import display as pico_display, i2c as pico_i2c, button_a, button_b, led
from board import P0, P1, P2, P8, P12, P13, P14, P15, P16, P19, P20
from time import monotonic_ns, sleep as time_sleep
from digitalio import DigitalInOut, Direction
from gc import collect as gc_collect
from analogio import AnalogIn
from lcd_api import LcdApi
from pwmio import PWMOut
from math import pi

PI = pi	
TWO_PI = 2*pi
HALF_PI = pi/2

# JoyCar konstanty
I2C_ADDR_MOTION = 0x70
I2C_ADDR_SENZORS = 0x38
I2C_ADDR_LCD = 0x27

LCD_NUM_ROWS = 4
LCD_NUM_COLS = 20

TICKS_PER_CIRCLE = 40
WHEEL_DIAMETER = 0.067
ROBOT_DIAMETER = 0.15


class I2C:
    def __init__(self) -> None:
        self.picoed_i2c = pico_i2c

    def init(self, freq:int=100_000, sda=P20, scl=P19) -> None:
        # pouzivame uz existujici objekt i2c z picoed-u, takze ho nebudeme inicializovat
        pass

    def __lock(self) -> None:
        while not self.picoed_i2c.try_lock():
            pass

    def __unlock(self) -> None:
        self.picoed_i2c.unlock()

    def scan(self) -> list[int]:
        self.__lock()
        ret = self.picoed_i2c.scan()
        self.__unlock()
        return ret

    def read(self, addr:int, n:int, repeat:bool=False) -> bytearray:
        self.__lock()
        buffer = bytearray(n)
        self.picoed_i2c.readfrom_into(addr, buffer, start=0, end=n)
        self.__unlock()
        return buffer

    def write(self, addr:int, buf:bytearray, repeat:bool=False) -> None:
        self.__lock()
        self.picoed_i2c.writeto(addr, buf)
        self.__unlock()

    def write_readinto(self, addr:int, write_buf:bytearray, read_buf:bytearray) -> None:
        self.__lock()
        self.picoed_i2c.writeto_then_readfrom(addr, write_buf, read_buf)
        self.__unlock()

i2c = I2C()

class PinPWM:
    def __init__(self, pin) -> None:
        self.pinName = pin
        self.pwm = None

    def set_analog_period(self, periodMS: int) -> None:
        if self.pwm:
            self.pwm.deinit()  # Uvolní předchozí objekt PWM
        freq = round(1000 / periodMS)  # Lepší přepočet periody na frekvenci
        self.pwm = PWMOut(self.pinName, frequency=freq)

    def write_analog(self, value) -> None:
        if self.pwm:
            self.pwm.duty_cycle = int(value)

    def read_analog(self, value) -> None:
        #FIXME
        if self.pwm:
            self.pwm.duty_cycle = int(value)

class PinDigital:
    def __init__(self, pin) -> None:
        self.pinName = pin
        self.pin = DigitalInOut(self.pinName)

    def read_digital(self) -> int:
        if self.pin.value:
            return 1
        return 0

    def write_digital(self, value) -> None:
        self.pin.direction = Direction.OUTPUT
        self.pin.value = (value!=1)

class PinADC:
    def __init__(self, pin) -> None:
        self.pinName = pin
        self.pin = AnalogIn(self.pinName)

    def read_analog(self) -> int:
        print(self.pin.value)
        return self.pin.value // 64

pin0 = P0
pin1 = PinPWM(P1)
pin2 = PinADC(P2)
pin8 = PinDigital(P8)
pin12 = PinDigital(P12)
pin13 = PinPWM(P13)
pin14 = PinDigital(P14)
pin15 = PinDigital(P15)
pin16 = PinPWM(P16)

def sleep(ms) -> None:
    time_sleep(ms / 1000)

def ticks_ms() -> int:
    return adf_ticks_ms()

def ticks_us() -> int:
    return monotonic_ns() // 1_000

def ticks_diff(ticks1:int, ticks2:int) -> int:
    return adf_ticks_diff(ticks1, ticks2)

def time_pulse_us(pin, pulse_level: int, timeout_us=1_000_000) -> int:
    start = ticks_us()
    while pin.read_digital() != pulse_level:
        if ticks_diff(ticks_us(), start) > timeout_us:
            return -1  # Timeout
    start = ticks_us()
    while pin.read_digital() == pulse_level:
        if ticks_diff(ticks_us(), start) > timeout_us:
            return -1  # Timeout
    return ticks_diff(ticks_us(), start)

# PCF8574 pin definitions
MASK_RS = 0x01       # P0
MASK_RW = 0x02       # P1
MASK_E  = 0x04       # P2
SHIFT_BACKLIGHT = 3  # P3
SHIFT_DATA      = 4  # P4-P7

class I2cLcd(LcdApi):   
    #Implements a HD44780 character LCD connected via PCF8574 on I2C
    def __init__(self, i2c:I2C, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.i2c.write(self.i2c_addr, bytes([0]))
        sleep(20)   # Allow LCD time to powerup
        # Send reset 3 times
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep(5)    # Need to delay at least 4.1 msec
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep(1)
        self.hal_write_init_nibble(self.LCD_FUNCTION_RESET)
        sleep(1)
        # Put LCD into 4-bit mode
        self.hal_write_init_nibble(self.LCD_FUNCTION)
        sleep(1)
        LcdApi.__init__(self, num_lines, num_columns)
        cmd = self.LCD_FUNCTION
        if num_lines > 1:
            cmd |= self.LCD_FUNCTION_2LINES
        self.hal_write_command(cmd)
        gc_collect()

    def hal_write_init_nibble(self, nibble):
        # Writes an initialization nibble to the LCD.
        # This particular function is only used during initialization.
        byte = ((nibble >> 4) & 0x0f) << SHIFT_DATA
        self.i2c.write(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.write(self.i2c_addr, bytes([byte]))
        gc_collect()
        
    def hal_backlight_on(self):
        # Allows the hal layer to turn the backlight on
        self.i2c.write(self.i2c_addr, bytes([1 << SHIFT_BACKLIGHT]))
        gc_collect()
        
    def hal_backlight_off(self):
        #Allows the hal layer to turn the backlight off
        self.i2c.write(self.i2c_addr, bytes([0]))
        gc_collect()
        
    def hal_write_command(self, cmd):
        # Write a command to the LCD. Data is latched on the falling edge of E.
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                (((cmd >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.write(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.write(self.i2c_addr, bytes([byte]))
        byte = ((self.backlight << SHIFT_BACKLIGHT) |
                ((cmd & 0x0f) << SHIFT_DATA))
        self.i2c.write(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.write(self.i2c_addr, bytes([byte]))
        if cmd <= 3:
            # The home and clear commands require a worst case delay of 4.1 msec
            sleep(5)
        gc_collect()

    def hal_write_data(self, data):
        # Write data to the LCD. Data is latched on the falling edge of E.
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                (((data >> 4) & 0x0f) << SHIFT_DATA))
        self.i2c.write(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.write(self.i2c_addr, bytes([byte]))
        byte = (MASK_RS |
                (self.backlight << SHIFT_BACKLIGHT) |
                ((data & 0x0f) << SHIFT_DATA))      
        self.i2c.write(self.i2c_addr, bytes([byte | MASK_E]))
        self.i2c.write(self.i2c_addr, bytes([byte]))
        gc_collect()

    def obrazovka1(self):
        self.move_to(0, 0)
        self.putstr("   position odometry")
        self.move_to(0, 1)
        self.putstr("x:")
        self.move_to(0, 2)
        self.putstr("y:")
        self.move_to(0, 3)
        self.putstr("t:")

    def writePosition(self, x:int, y:int, theta:int) -> None:
        self.obrazovka1()
        self.move_to(3, 1)
        self.putstr("{:3d}".format(x))
        self.move_to(3, 2)
        self.putstr("{:3d}".format(y))
        self.move_to(3, 3)
        self.putstr("{:3d}".format(theta))

    def writeOdometry(self, x:float, y:float, theta:int) -> None:
        self.move_to(12, 1)
        self.putstr("{:5.3f}".format(x))
        self.move_to(12, 2)
        self.putstr("{:5.3f}".format(y))
        self.move_to(12, 3)
        self.putstr("{:3d}".format(theta))

# lcd = I2cLcd(i2c, I2C_ADDR_LCD, LCD_NUM_ROWS, LCD_NUM_COLS)

class Battery:
    @staticmethod
    def getSupplyVoltage() -> float:
        # vrať velikost napájecího napětí 
        return 0.00898 * pin2.read_analog() 

class Display:

    @staticmethod
    def supplyVoltage() -> None:
        voltage = Battery.getSupplyVoltage()
        powerSupply = "{:1.1f} V".format(voltage)
        print("Napájecí napětí:",powerSupply)
        Display.__iconA(powerSupply[0])
        Display.decimalPointAfterA(True)
        Display.__iconB(powerSupply[2])
        Display.__iconC(powerSupply[4])


    rowsDisp = 7
    colsDisp = 17

    # Inicializace pixelsMap v metodě třídy nebo přes konstruktor
    __pixelsMap = None
    __redrawNeeded = None

    @classmethod
    def __initialize(cls) -> None:
        print('System.initialize')
        cls.__pixelsMap = [bytearray(cls.colsDisp) for _ in range(cls.rowsDisp)]
        cls.__redrawNeeded = [[True for _ in range(cls.colsDisp)] for _ in range(cls.rowsDisp)]

    @staticmethod
    def clear() -> None:
        pico_display.fill(0)
        for row in Display.__pixelsMap:
            for col in range(len(row)):
                row[col] = 0

    @staticmethod
    def pixel(col:int, row:int, color:int) -> None:
        if 0 <= col < Display.colsDisp:
            if 0 <= row < Display.rowsDisp:
                oldColor = Display.__pixelsMap[row][col]
                Display.__pixelsMap[row][col] = color
                Display.__redrawNeeded[row][col] |= (color != oldColor)
    
    @staticmethod
    def redraw() -> None:
        for _ in range(119):
            Display.__updatePixel()

    __currectCol = 0
    __currectRow = 0
    @staticmethod
    def updatePixels() -> bool:
        ret1 = Display.__updatePixel()
        ret2 = Display.__updatePixel()
        return ret1 or ret2

    @staticmethod
    def __updatePixel() -> bool:
        for _ in range(20):
            if Display.__updatePixelCondition():
                return True
        return False

    @staticmethod
    def __updatePixelCondition() -> bool:
        col = Display.__currectCol
        row = Display.__currectRow
        Display.__currectCol += 1
        if Display.__currectCol >= Display.colsDisp:
            Display.__currectCol = 0
            Display.__currectRow += 1
            if Display.__currectRow >= Display.rowsDisp:
                Display.__currectRow = 0
        if Display.__redrawNeeded[row][col]:
            Display.__redrawNeeded[row][col] = False
            pico_display.pixel(col, row, Display.__pixelsMap[row][col])
            return True
        return False


    __PICTOGRAMS = {
        '>':  [0b00100, 0b00010, 0b11111, 0b00010, 0b00100],  # zatočení doprava
        '<':  [0b00100, 0b01000, 0b11111, 0b01000, 0b00100],  # zatočení doleva
        '^':  [0b00100, 0b00100, 0b10101, 0b01110, 0b00100],  # jedeme rovně
        'v':  [0b00100, 0b01110, 0b10101, 0b00100, 0b00100],  # jedeme zpátky
        'TL': [0b00100, 0b00100, 0b11100, 0b00000, 0b00000],  # rohová křižovatka doleva (turn to left)
        'TR': [0b00100, 0b00100, 0b00111, 0b00000, 0b00000],  # rohová křižovatka doprava (turn to right)
        'IT': [0b00100, 0b00100, 0b11111, 0b00000, 0b00000],  # intersection left-right (T)
        'IL': [0b00100, 0b00100, 0b11100, 0b00100, 0b00100],  # intersection left-straight (T to left)
        'IR': [0b00100, 0b00100, 0b00111, 0b00100, 0b00100],  # intersection right-straight (T to right)
        'I+': [0b00100, 0b00100, 0b11111, 0b00100, 0b00100],  # intersection all directions (+)
        '--': [0b00000, 0b00000, 0b11111, 0b00000, 0b00000],
        ' -': [0b00000, 0b00000, 0b00111, 0b00000, 0b00000],
        '- ': [0b00000, 0b00000, 0b11100, 0b00000, 0b00000],
        '_':  [0b11111, 0b00000, 0b00000, 0b00000, 0b00000],
        '.':  [0b00100, 0b00000, 0b00000, 0b00000, 0b00000],
        '|':  [0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
        '/':  [0b10000, 0b01000, 0b00100, 0b00010, 0b00001],
        '\\': [0b00001, 0b00010, 0b00100, 0b01000, 0b10000],
        's':  [0b11100, 0b00010, 0b01110, 0b01000, 0b00111],
        'x':  [0b10001, 0b01010, 0b00100, 0b01010, 0b10001],
        ' ':  [0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
        ',':  [0b00100, 0b00010, 0b00000, 0b00000, 0b00000],
        '0':  [0b01110, 0b01010, 0b01010, 0b01010, 0b01110],
        '1':  [0b00100, 0b00100, 0b00100, 0b01100, 0b00100],
        '2':  [0b01110, 0b01000, 0b01110, 0b00010, 0b01110],
        '3':  [0b01110, 0b00010, 0b00110, 0b00010, 0b01110],
        '4':  [0b00010, 0b00010, 0b01110, 0b01010, 0b01010],
        '5':  [0b01110, 0b00010, 0b01110, 0b01000, 0b01110],
        '6':  [0b01110, 0b01010, 0b01110, 0b01000, 0b01110],
        '7':  [0b00010, 0b00010, 0b00010, 0b00010, 0b01110],
        '8':  [0b01110, 0b01010, 0b01110, 0b01010, 0b01110],
        '9':  [0b01110, 0b00010, 0b01110, 0b01010, 0b01110],

        'A':  [0b01010, 0b01010, 0b01110, 0b01010, 0b00100],
        'B':  [0b01100, 0b01010, 0b01100, 0b01010, 0b01100],
        'C':  [0b00110, 0b01000, 0b01000, 0b01000, 0b00110],
        'D':  [0b01100, 0b01010, 0b01010, 0b01010, 0b01100],
        'E':  [0b01110, 0b01000, 0b01100, 0b01000, 0b01110],
        'F':  [0b01000, 0b01000, 0b01100, 0b01000, 0b01110],
        # 'G':  [0b00110, 0b01010, 0b01000, 0b01000, 0b00110],
        'H':  [0b01010, 0b01010, 0b01110, 0b01010, 0b01010],
        'I':  [0b01110, 0b00100, 0b00100, 0b00100, 0b01110],
        'J':  [0b00100, 0b01010, 0b00010, 0b00010, 0b00010],
        # 'K':  [0b01010, 0b01100, 0b01000, 0b01100, 0b01010],
        # 'L':  [0b01110, 0b01000, 0b01000, 0b01000, 0b01000],
        # 'M':  [0b01010, 0b01010, 0b01110, 0b01110, 0b01010],
        # 'N':  [0b01010, 0b01110, 0b01110, 0b01010, 0b01010],
        # 'O':  [0b00100, 0b01010, 0b01010, 0b01010, 0b00100],
        # 'P':  [0b01000, 0b01000, 0b01100, 0b01010, 0b01100],
        # 'Q':  [0b00110, 0b01110, 0b01010, 0b01010, 0b00100],
        # 'R':  [0b01010, 0b01100, 0b01100, 0b01010, 0b01100],
        # 'S':  [0b01100, 0b00010, 0b00100, 0b01000, 0b00110],
        # 'T':  [0b00100, 0b00100, 0b00100, 0b00100, 0b11111],
        # 'U':  [0b00100, 0b01010, 0b01010, 0b01010, 0b01010],
        'V':  [0b00100, 0b01010, 0b01010, 0b01010, 0b01010],
        # 'W':  [0b01010, 0b01110, 0b01010, 0b01010, 0b01010],
        # 'X':  [0b01010, 0b01010, 0b00100, 0b01010, 0b01010],
        'Y':  [0b00100, 0b00100, 0b00100, 0b01010, 0b01010],
        'Z':  [0b01110, 0b01000, 0b00100, 0b00010, 0b01110],

    }

    @staticmethod
    def number(num: int) -> None:
        number = "{:3d}".format(num)  # 3 znaky, pokud je číslo kratší, přidá mezery
        Display.iconA(number[0])
        Display.iconB(number[1])
        Display.iconC(number[2])

    @staticmethod
    def __bitmap(x_pos: int, y_pos: int, width: int, lines: list[int]) -> None:
        hight = len(lines)
        for iy in range(hight):
            line = lines[iy]
            y = y_pos + iy
            for ix in range(width):
                pixel = line & (1 << ix)
                color = 3 if pixel else 0
                x = x_pos + ix
                Display.pixel(x, y, color)

    @staticmethod
    def __decimalPoint(show:bool, x_poz:int, y_poz:int=0, color:int=9) -> None:
        Display.pixel(x_poz, y_poz, color if show else 0)

    @staticmethod
    def __iconA(icon: str) -> None:
        Display.__bitmap(12, 0, 5, Display.__PICTOGRAMS[icon])

    @staticmethod
    def decimalPointAfterA(show:bool) -> None:
        Display.__decimalPoint(show, 11)

    @staticmethod
    def __iconB(icon: str) -> None:
        Display.__bitmap(6, 0, 5, Display.__PICTOGRAMS[icon])

    @staticmethod
    def decimalPointAfterB(show: bool) -> None:
        Display.__decimalPoint(show, 5)

    @staticmethod
    def __iconC(icon: str) -> None:
        Display.__bitmap(0, 0, 5, Display.__PICTOGRAMS[icon])

    @staticmethod
    def drive_mode(mode: str) -> None:
        Display.__iconB(mode)

    @staticmethod
    def position(x: int, y: int) -> None:
        x_char = str(min(9, int(x)))
        y_char = str(min(9, int(y)))
        Display.__iconA(x_char)
        Display.__iconC(y_char)

    @staticmethod
    def positionEmpty() -> None:
        Display.__iconA(" ")
        Display.__iconC(" ")

    @staticmethod
    def senzors(obstacleLeft:bool, farLeft:bool, left:bool, midleLeft:bool, midle35:bool, midleRight:bool, right:bool, farRight:bool, obstacleRight:bool, bh:int, bl:int) -> None:
        Display.pixel(16, 6, bh if obstacleLeft   else bl)

        if farLeft is not None:
            Display.pixel(13, 6, bh if farLeft    else bl)

        Display.pixel(11, 6, bh if left           else bl)

        if farRight is not None:
            Display.pixel( 3, 6, bh if farRight   else bl)
        if midleLeft is not None:
            Display.pixel( 9, 6, bh if midleLeft  else bl)
        if midle35 is not None:
            Display.pixel( 8, 6, bh if midle35    else bl)

        Display.pixel( 5, 6, bh if right          else bl)

        if midleRight is not None:            
            Display.pixel( 7, 6, bh if midleRight else bl)

        Display.pixel( 0, 6, bh if obstacleRight  else bl)

# Inicializace pixelsMap voláním metody initialize
Display.__initialize()
