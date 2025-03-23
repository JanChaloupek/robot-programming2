from HardwarePlatform import display, pin2, ticks_us

class System:

    rowsDisp = 7
    colsDisp = 17

    # Inicializace pixelsMap v metodě třídy nebo přes konstruktor
    pixelsMap = None
    redrawNeeded = None

    @classmethod
    def initialize(cls):
        print('System.initialize')
        cls.pixelsMap = [bytearray(cls.colsDisp) for _ in range(cls.rowsDisp)]
        cls.redrawNeeded = [[True for _ in range(cls.colsDisp)] for _ in range(cls.rowsDisp)]

    @staticmethod
    def display_pixel(col, row, color):
        if 0 <= col < System.colsDisp:
            if 0 <= row < System.rowsDisp:
                oldColor = System.pixelsMap[row][col]
                System.pixelsMap[row][col] = color
                System.redrawNeeded[row][col] = (color != oldColor)
    
    __currectCol = 0
    __currectRow = 0
    @staticmethod
    def updatePixels():
        System.updatePixel()
        System.updatePixel()
        System.updatePixel()

    @staticmethod
    def updatePixel() -> bool:
        for _ in range(20):
            if System.updatePixelCondition():
                return

    @staticmethod
    def updatePixelCondition() -> bool:
        col = System.__currectCol
        row = System.__currectRow
        System.__currectCol += 1
        if System.__currectCol >= System.colsDisp:
            System.__currectCol = 0
            System.__currectRow += 1
            if System.__currectRow >= System.rowsDisp:
                System.__currectRow = 0
        if System.redrawNeeded[row][col]:
            display.pixel(col, row, System.pixelsMap[row][col])
            System.redrawNeeded[row][col] = False
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

        # 'A':  [0b01010, 0b01010, 0b01110, 0b01010, 0b00100],
        # 'B':  [0b01100, 0b01010, 0b01100, 0b01010, 0b01100],
        # 'C':  [0b00110, 0b01000, 0b01000, 0b01000, 0b00110],
        # 'D':  [0b01100, 0b01010, 0b01010, 0b01010, 0b01100],
        'E':  [0b01110, 0b01000, 0b01100, 0b01000, 0b01110],
        # 'F':  [0b01000, 0b01000, 0b01100, 0b01000, 0b01110],
        # 'G':  [0b00110, 0b01010, 0b01000, 0b01000, 0b00110],
        # 'H':  [0b01010, 0b01010, 0b01110, 0b01010, 0b01010],
        # 'I':  [0b01110, 0b00100, 0b00100, 0b00100, 0b01110],
        # 'J':  [0b00100, 0b01010, 0b00010, 0b00010, 0b00010],
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
        # 'Y':  [0b00100, 0b00100, 0b00100, 0b01010, 0b01010],
        # 'Z':  [0b01110, 0b01000, 0b00100, 0b00010, 0b01110],

    }

    @staticmethod
    def getSupplyVoltage() -> float:
        # vrať velikost napájecího napětí 
        return 0.00898 * pin2.read_analog() 

    @staticmethod
    def display_SupplyVoltage():
        print("Supply")
        voltage = System.getSupplyVoltage()
        powerSupply = "{:1.1f} V".format(voltage)
        print(powerSupply)
        print("Napájecí napětí:",powerSupply)
        System.display_iconA(powerSupply[0])
        System.display_decimalPointAfterA(True)
        System.display_iconB(powerSupply[2])
        System.display_iconC(powerSupply[4])

    @staticmethod
    def __display_bitmap(x_pos: int, y_pos: int, width: int, lines: list[int]):
        hight = len(lines)
        for iy in range(hight):
            line = lines[iy]
            y = y_pos + iy
            for ix in range(width):
                pixel = line & (1 << ix)
                color = 9 if pixel else 0
                x = x_pos + ix
                System.display_pixel(x, y, color)

    @staticmethod
    def display_clear():
        display.fill(0)
        for row in System.pixelsMap:
            for col in range(len(row)):
                row[col] = 0

    @staticmethod
    def display_decimalPoint(show:bool, x_poz:int, y_poz:int=0, color:int=9):
        System.display_pixel(x_poz, y_poz, color if show else 0)

    @staticmethod
    def __display_iconA(icon: str):
        System.__display_bitmap(11, 0, 5, System.__PICTOGRAMS[icon])

    @staticmethod
    def display_decimalPointAfterA(show:bool):
        System.display_decimalPoint(show, 11)

    @staticmethod
    def __display_iconB(icon: str):
        System.__display_bitmap(6, 0, 5, System.__PICTOGRAMS[icon])

    @staticmethod
    def display_decimalPointAfterB(show: bool):
        System.display_decimalPoint(show, 6)

    @staticmethod
    def __display_iconC(icon: str):
        System.__display_bitmap(1, 0, 5, System.__PICTOGRAMS[icon])

    @staticmethod
    def display_decimalPointAfterC(show: bool):
        System.display_decimalPoint(show, 1)

    @staticmethod
    def display_drive_mode(mode: str):
        System.__display_iconB(mode)

    @staticmethod
    def display_position(x: int, y: int):
        x_char = str(min(9, int(x)))
        y_char = str(min(9, int(y)))
        System.__display_iconA(x_char)
        System.__display_iconC(y_char)

    @staticmethod
    def display_senzors(obstacleLeft:bool, farLeft:bool, left:bool, midleLeft:bool, midle35:bool, midleRight:bool, right:bool, farRight:bool, obstacleRight:bool, bh:int, bl:int):
        System.display_pixel(16, 6, bh if obstacleLeft   else bl)

        if farLeft is not None:
            System.display_pixel(13, 6, bh if farLeft    else bl)

        System.display_pixel(11, 6, bh if left           else bl)

        if farRight is not None:
            System.display_pixel( 3, 6, bh if farRight   else bl)
        if midleLeft is not None:
            System.display_pixel( 9, 6, bh if midleLeft  else bl)
        if midle35 is not None:
            System.display_pixel( 8, 6, bh if midle35    else bl)

        System.display_pixel( 5, 6, bh if right          else bl)

        if midleRight is not None:            
            System.display_pixel( 7, 6, bh if midleRight else bl)

        System.display_pixel( 0, 6, bh if obstacleRight  else bl)

# Inicializace pixelsMap voláním metody initialize
System.initialize()
